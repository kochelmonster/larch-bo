# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("@floating-ui/dom")
def require(*args): pass
# __pragma__("noskip")


floating = require('@floating-ui/dom')
