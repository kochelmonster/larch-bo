import sys
from larch.lib.aspect import aspect
from larch.bo.server.application import ApplicationPointcut


class InformFrontend(aspect(ApplicationPointcut)):
    """
    Checks if a session task needs too long, and causes the
    Application to be unreactive.
    """

    def __init__(self, application):
        super().__init__(application.pointcut)
        application._inform_frontend_aspect = self

    def start(self, server):
        port = server.socket.getsockname()[1]
        sys.stderr.write(f"http://localhost:{port}/index.html\n")
