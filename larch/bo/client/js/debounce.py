# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("lodash.debounce")
def require(*args): pass
# __pragma__("noskip")


debounce = require('lodash.debounce')
