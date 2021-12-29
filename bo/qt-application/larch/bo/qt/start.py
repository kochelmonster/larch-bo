"""PySide6 WebEngineWidgets Example"""
import os
import sys
import argparse
from pathlib import Path


def local_parser():
    choices = ['local', 'server', 'debug', 'compile', 'test']
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--type', help='application type', choices=choices, default='local')
    parser.add_argument('--left', type=int, help='left corner of window')
    parser.add_argument('--top', type=int, help='top corner of window')
    parser.add_argument('--width', type=int, help='width of window')
    parser.add_argument('--height', type=int, help='height of window')
    parser.add_argument('--remote-debugging-port', type=int, default=8228)
    parser.add_argument("--path", help="path of start url")
    return parser


def run(root, config=None, application=None):
    arg_parser = local_parser()
    args = arg_parser.parse_known_args()[0]
    try:
        type_ = args.type
    except AttributeError:
        type_ = "local"   # a frozen version without this option

    if type_ in ("compile", "server", "debug"):
        from larch.bo.server import run
        config = config or {}
        config["wsheartbeat"] = 0  # websocket heartbeat not needed
        config["runtype"] = "local"
        return run(root, config, application)

    if os.environ.get("LARCH_BO_QT_FRONTEND_STARTED"):
        from larch.bo.server import run
        from .pointcuts import InformFrontend
        config.setdefault("application_pointcuts", []).append(InformFrontend)
        sys.argv.append("--port=0")
        return run(root, config, application)
    else:
        from subprocess import Popen, PIPE
        from .window import start_frontend
        config = config or {}
        config["args"] = args

        config.setdefault("resources_path", Path(
            config.get("build_path") or Path.cwd().resolve()/".lfrontend")/"dist")

        args = [sys.executable] + sys.argv
        new_environ = os.environ.copy()
        new_environ["LARCH_BO_QT_FRONTEND_STARTED"] = "server"
        server_process = Popen(args, env=new_environ, stderr=PIPE, close_fds=True, encoding="utf8")
        url = server_process.stderr.readline().strip()
        try:
            return start_frontend(url, config)
        finally:
            server_process.terminate()
