"""some helpfull methods for debugging."""
from __future__ import print_function
import gevent
import sys
import weakref
import os
import logging
import traceback
import greenlet
import gevent.hub
import time
import site
from itertools import chain
from gevent.event import AsyncResult
from gevent import subprocess, monkey, getcurrent, kill
from watchdog_gevent import Observer
from watchdog.events import FileSystemEventHandler
from contextlib import contextmanager

logger = logging.getLogger('larch.ui')
del logging

PY2 = sys.version_info[0] == 2


monkey.patch_all()


class CheckFiles(FileSystemEventHandler):
    def __init__(self, files):
        self.changed_file = AsyncResult()

    def on_modified(self, event):
        self.changed_file.set(event.src_path)


def run_with_reloader(main_func, extra_files=None, interval=1):
    """Run the given function in an independent python interpreter."""
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        reloader_greenlet = getcurrent()
        main_greenlet = gevent.spawn(main_func)

        def kill_me(*args):
            kill(reloader_greenlet)

        main_greenlet.link(kill_me)
        result = 1
        try:
            result = reloader_loop(extra_files, interval)
        except BaseException:
            return 1
        finally:
            main_greenlet.unlink(kill_me)
            main_greenlet.kill()
        return result

    return restart_with_reloader()


def restart_with_reloader():
    """Spawn a new Python interpreter with the same arguments as this one,
    but running the reloader thread.
    """
    while True:
        logger.info("Restarting with reloader %r", os.getpid())
        args = [sys.executable] + sys.argv
        new_environ = os.environ.copy()
        new_environ['WERKZEUG_RUN_MAIN'] = 'true'

        # a weird bug on windows. sometimes unicode strings end up in the
        # environment and subprocess.call does not like this, encode them
        # to latin1 and continue.
        if os.name == 'nt' and PY2:
            for key, value in new_environ.items():
                if not isinstance(value, bytes):
                    new_environ[key] = value.encode('iso-8859-1')

        try:
            process = subprocess.Popen(args, env=new_environ)
            process.wait()
        except KeyboardInterrupt:
            print("restart with reloader KeyboardInterrupt")
            process.terminate()
            return 2

        exit_code = process.returncode
        print("restart with reloader child process exit", exit_code)
        if exit_code != 7:
            return exit_code


def wait_for_change(files):
    event_handler = CheckFiles(files)

    observer = Observer()
    for f in files:
        observer.schedule(event_handler, f, False)

    observer.start()
    try:
        return event_handler.changed_file.get()
    finally:
        observer.stop()


def reloader_loop(extra_files=None, interval=1):
    """see werkzeug"""

    site_dirs = site.getsitepackages()
    site_dirs.append(os.path.dirname(site.__file__))

    files = [f for f in chain(_iter_module_files(), extra_files or ())
             if not any(f.startswith(s) for s in site_dirs)]
    try:
        if wait_for_change(files):
            return 7
    except KeyboardInterrupt:
        return 2


def _iter_module_files():
    # The list call is necessary on Python 3 in case the module
    # dictionary modifies during iteration.
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            old = None
            while not os.path.isfile(filename):
                old = filename
                filename = os.path.dirname(filename)
                if filename == old:
                    break
            else:
                if filename[-4:] in ('.pyc', '.pyo'):
                    filename = filename[:-1]
                yield filename


class ObjectTracer(object):
    def __init__(self):
        self.objs = {}
        self.counter = 0

    def register(self, obj, name=None):
        name = name or repr(obj)
        print('**register', name)
        self.objs[weakref.ref(obj, self.remove)] = name, self.counter
        self.counter += 1

    def remove(self, ref):
        name = self.objs[ref]
        print('**remove', name)
        del self.objs[ref]
        return
        if 'View' in name[0]:
            import gc
            import pprint
            pprint.pprint(list(self.objs.values()), width=100)

            def print_referrers(o):
                print('referrers of', o)
                refs = gc.get_referrers(o)
                pprint.pprint(refs, width=100)
                return refs

            for k, (name, count) in self.objs.items():
                if count == 3:
                    print('-----name', k())
                    refs = print_referrers(k())
                    refs = print_referrers(refs[1])


tracer = ObjectTracer()


@contextmanager
def profile(fname):
    import GreenletProfiler
    GreenletProfiler.start(True)
    try:
        yield
    finally:
        GreenletProfiler.stop()
        stats = GreenletProfiler.get_func_stats()
        stats.save(fname, type="callgrind")


_patched_double_rendering = False


def profile_find_double_rendering():
    """monkey patch session to find multiple renderings of one view.
    This may be a performance issue"""
    from larch.ui.viewer import View
    global _patched_double_rendering

    if _patched_double_rendering:
        return

    _patched_double_rendering = True

    old_paint = View._paint

    def patched_paint(self):
        try:
            response_id, control = self._profile_last_paint
        except AttributeError:
            pass
        else:
            if response_id == self.session.response_id and "NoneControl" not in control:
                print("double render", self, control, "->", self.control)

        self._profile_last_paint = self.session.response_id, repr(self.control)
        old_paint(self)

    View._paint = patched_paint


class SwitchTracer(object):
    """
    Provides a trace function that gets executed on every greenlet switch.
    It checks how much time has elapsed and logs an error if it was excessive.
    The Hub gets an exemption, because it's allowed to block on I/O.
    """

    MAX_BLOCKING_TIME = 0.1
    """The maximum amount of time that the eventloop can be blocked
    without causing an error to be logged, in seconds."""

    _last_switch_time = None
    max_switch_time = 0

    @contextmanager
    def __call__(self):
        old_trace = greenlet.settrace(self._switch_time_tracer)
        try:
            yield
        finally:
            greenlet.settrace(old_trace)
            print("Maximal switch time", self.max_switch_time, file=sys.stderr)

    def _switch_time_tracer(self, what, origin_target):
        (origin, target) = origin_target
        then = self._last_switch_time
        now = self._last_switch_time = time.time()
        if then is not None:
            blocking_time = now - then
            if origin is not gevent.hub.get_hub():
                self.max_switch_time = max(self.max_switch_time, blocking_time)
                if blocking_time > self.MAX_BLOCKING_TIME:
                    msg = "Greenlet blocked the eventloop for %.4f seconds\n"
                    msg = msg % (blocking_time, )
                    print(msg, origin, file=sys.stderr)
                    traceback.print_stack(origin.gr_frame)


@contextmanager
def debug_switch():
    current = gevent.getcurrent()

    def log_switch(what, origin_target):
        (origin, target) = origin_target
        if origin is current:
            print("switch away from", origin)
            traceback.print_stack(origin.gr_frame)

    old_trace = greenlet.settrace(log_switch)
    try:
        yield 1
    finally:
        greenlet.settrace(old_trace)
