"""PySide6 WebEngineWidgets Example"""
import os
import sys
import argparse
import socket
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


def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def run(root, config=None, application=None):
    arg_parser = local_parser()
    args = arg_parser.parse_known_args()[0]
    try:
        type_ = args.type
    except AttributeError:
        type_ = "local"   # a frozen version without this option

    if type_ in ("compile", "server"):
        from larch.bo.server import run
        config = config or {}
        config["wsheartbeat"] = 0  # websocket heartbeat not needed
        config["runtype"] = "local"
        return run(root, config, application)

    if os.environ.get("LARCH_BO_QT_FRONTEND_STARTED"):
        from larch.bo.server import run
        return run(root, config, application)
    else:
        from subprocess import Popen
        from .window import start_frontend
        config = config or {}
        config["args"] = args

        resource_path = config.setdefault("resource_path", Path(
            config.get("build_path") or Path.cwd().resolve()/".lfrontend")/"dist")

        if config.get("debug", False) and type_ != "debug":
            from larch.bo.server.start import check_for_compile
            config["root"] = root
            check_for_compile(config)

        url = "file://" + str(Path(resource_path)/"index.html")
        if config.get("transmitter") or type_ == "debug":
            port = get_free_port()
            args = [sys.executable] + sys.argv + [f"--port={port}"]
            new_environ = os.environ.copy()
            new_environ["LARCH_BO_QT_FRONTEND_STARTED"] = "server"
            new_environ["LARCH_START"] = "qt-server"
            server_process = Popen(args, env=new_environ, encoding="utf8")
            url += f"?transmitter={port}"
            try:
                return start_frontend(url, config, type_ == "debug")
            finally:
                server_process.terminate()
        else:
            return start_frontend(url, config)
