"""startup code for larch.ui"""
import argparse
import sys
import os
import logging
from pathlib import Path
from importlib import import_module

logger = logging.getLogger('larch.bo.server')
del logging

DEFAULT_SERVER = "larch.bo.server.gevent"

# Note:
#   application is any wsgi application object. It can be a wsgi middleware
#     component that wraps application (i.e wsgigzip):
#       >>> run(application=GzipMiddleware(Application(config)))


def server_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--port', type=int, help='server ip port', default=8080)
    parser.add_argument('--interface', help='server interface', default='')
    parser.add_argument("--pid-file", help='path to pid file', default='')
    return parser


def all_parser():
    choices = ['server', 'debug', 'compile', 'test']
    parser = argparse.ArgumentParser(parents=[server_parser()])
    parser.add_argument('--type', help='application type', choices=choices, default='server')
    parser.add_argument("--recompile", action='store_true',
                        help="recompiles the resource file before execution")
    parser.add_argument("--no-module", action='store_true',
                        help="Do no load javscript as module. This option allows index.html to "
                        "load as file. Works only with --type=compile")
    return parser


def check_for_compile(config):
    from larch.bo.packer import compile_resources
    force = config.get("runtype") == "compile"
    if not force:
        try:
            force = config["args"].recompile
        except (AttributeError, KeyError):
            force = False

    logger.info("recompile resources %r", force)
    return compile_resources(config, force)


def patch_gevent(config):
    if DEFAULT_SERVER == config.get("wsgi_server", DEFAULT_SERVER):
        from gevent import monkey
        monkey.patch_all()
        config["gevent"] = True


def run(root, config=None, application=None):
    config = config or {}
    patch_gevent(config)

    arg_parser = config.get("arg_parser", None) or all_parser()

    args = arg_parser.parse_known_args()[0]
    config["args"] = args

    if application is None:
        from .application import Application
        application = Application(config)

    if not isinstance(root, str):
        module = sys.modules[root.__module__]
        root = module.__file__

    config["root"] = root
    config.setdefault("resource_path", Path(
        config.get("build_path") or Path.cwd().resolve()/".lfrontend")/"dist")

    if os.environ.get("ANDROID_APP_PATH"):
        config["runtype"] = "android"
        config["wsheartbeat"] = 0  # not needed
        return run_android(application, config)

    try:
        type_ = args.type
    except AttributeError:
        type_ = "server"

    logger.info("start as %r", type_)
    if type_ == 'server':  # pragma: no cover
        config.setdefault("runtype", "server")
        if config.get("debug", False):
            check_for_compile(config)
        return run_server(application, config)
    elif type_ == 'compile':  # pragma: no cover
        from larch.bo.packer import compile_resources
        config["runtype"] = "compile"
        compile_resources(config, True)
        return 0
    elif type_ == 'test':
        config["runtype"] = "server"
        check_for_compile(config)
        return run_tests(application, config)
    else:  # pragma: no cover
        def run_debug():
            run_server(application, config)

        from .gevent.debug import run_with_reloader, wait_for_change, system_greenlets
        config.setdefault("build_path", Path(config["resource_path"]).parent)
        config["runtype"] = "debug"
        config['debug'] = True

        if not os.environ.get('WERKZEUG_RUN_MAIN'):
            from larch.bo.packer import start_watcher
            # check_for_compile(config)
            system_greenlets.extend(start_watcher(config, wait_for_change))

        return run_with_reloader(run_debug)

    return 1


def run_android(application, config):  # pragma: no cover
    config["debug"] = config["sources"] = False

    '''
    # still no way to load file:/// resources
    if config.get("extract_resources", True):
        from .resource.manager import extract_resources, get_resource_fname
        dest_dir = os.path.dirname(get_resource_fname(config))
        dest_dir = os.path.join(dest_dir, "resources")
        config.setdefault("resource_dir", dest_dir)
        extract_resources(config)
    '''

    config.setdefault('localrun', '')
    server = start_wsgi(application, config)
    port = server.socket.getsockname()[1]
    logger.info("started server at port: %r", port)
    try:
        server.serve_forever()
    finally:
        logger.info("shutdown app")
        application.shutdown()


def stop_server(config):
    server = config["application"].server
    if server is not None:
        server.close()
        return True

    return False


def run_server(application, config):
    args = config["args"]

    try:
        pid_file = args.pid_file
    except AttributeError:
        pid_file = None

    if pid_file:
        with open(pid_file, "wb") as f:
            f.write("{}\n".format(os.getpid()))

    try:
        interface = args.interface
    except AttributeError:
        interface = ""

    try:
        port = args.port
    except AttributeError:
        port = 0

    config.setdefault("address", (interface, port))
    config.setdefault('localrun', '')
    server = start_wsgi(application, config)
    try:
        server.serve_forever()
    finally:
        config["application"].shutdown()
        if pid_file:
            try:
                os.remove(pid_file)
            except OSError:
                pass

    return 0


def run_tests(application, config):
    import unittest
    from .test import SeleniumBase, driver
    SeleniumBase.application = application
    SeleniumBase.config = config
    argv = sys.argv[:]
    argv.remove("--type=test")
    try:
        argv.remove("--recompile")
    except ValueError:
        pass
    config['debug'] = True
    config['test'] = True
    try:
        result = unittest.main(argv=argv, failfast=True, exit=False).result.wasSuccessful()
    finally:
        logger.debug("##shutdown driver", stack_info=True)
        driver.shutdown()
    return 0 if result else -1


def start_wsgi(application, config):
    module = config.get("wsgi_server", DEFAULT_SERVER)

    if isinstance(module, str):
        module = import_module(module)

    server = module.start_wsgi(application, config)
    config["application"].start(server)
    logger.info('start wsgi server %r', config["address"])
    return server
