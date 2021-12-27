"""server communication modules"""

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.extend(["msgpack-lite"])
# __pragma__("noskip")
