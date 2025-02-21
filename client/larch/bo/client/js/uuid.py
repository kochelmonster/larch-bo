# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("uuid")
def require(*args): pass
# __pragma__("noskip")


uuid = require('uuid')
