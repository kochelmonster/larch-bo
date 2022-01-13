"""Tests for control module"""
from larch.bo.client.control import ControlContext
from larch.reactive import Reactive, rule, atomic

# __pragma__("skip")
# ---------------------------------------------------
import sys
from logging import getLogger
from larch.lib.test import config_logging
from larch.bo.server import run
from pathlib import Path

Date = Intl = window = document = console = None
logger = getLogger("main")
def require(path): pass
def __pragma__(*args): pass
def __new__(p): pass


if __name__ == "__main__":
    config_logging("hello.log", __file__)
    dir_ = Path(__file__).parent
    config = {
        "debug": True,
    }
    sys.exit(run(__file__, config=config))
# ---------------------------------------------------
# __pragma__ ("noskip")


class TestContext(Reactive):
    def __init__(self, context):
        self.context = context
        self.output = []

    def lap(self):
        output = self.output
        self.output = []
        return output

    def read(self):
        value = self.context.get("gval")
        self.output.append(f"read.get: {value}")

        for value in self.context.loop("lval"):
            self.output.append(f"read.loop: {value}")

        value = self.context.observe("oval")
        self.output.append(f"read.observe: {value}")
        return self

    @rule
    def _rule_test_get(self):
        value = self.context.get("gval")
        self.output.append(f"rule.get: {value}")

    @rule
    def _rule_test_loop(self):
        for value in self.context.loop("lval"):
            self.output.append(f"rule.loop: {value}")

    @rule
    def _rule_test_observer(self):
        value = self.context.observe("oval")
        self.output.append(f"rule.observe: {value}")


context = ControlContext()
test = TestContext(context)
console.log("init", test.lap())
console.log("read", test.read().lap())

context.set("gval", 1)
console.log("rule.gval", test.lap())

context.set("oval", 1)
console.log("rule.oval", test.lap())

context.set("lval", 1)
console.log("rule.lval", test.lap())

with atomic():
    context.set("lval", 2)
    context.set("oval", 2)

console.log("rule.lval/rule.oval", test.lap())

context.set("oval", 3)
console.log("next.rule.oval", test.lap())

context.set("lval", 4)
console.log("next.rule.lval", test.lap())

console.log("-------------------------------------")
