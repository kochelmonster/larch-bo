
# __pragma__("skip")
class Mock:
    protocol = origin = ""

    def createCodec(self, obj):
        pass

    def Decoder(self, obj):
        return self

    def Encoder(self):
        return self


location = Object = Mock()
def require(p): return Mock()
def __pragma__(*args): pass
def as_array(d): pass
# __pragma__("noskip")


msgpack = require("msgpack-lite")

__pragma__('js', '{}', '''
function as_array(data) {
    return new Uint8Array(data);
}
''')


class DecoderPipe:
    def __init__(self, push):
        self.codec = msgpack.createCodec({"preset": True, "safe": False})
        self.decoder = msgpack.Decoder({"codec": self.codec})
        self.decoder.push = push

    def write(self, data):
        self.decoder.write(as_array(data))
        self.decoder.flush()


class EncoderPipe:
    def __init__(self, push):
        self.encoder = msgpack.Encoder()
        self.encoder.push = push

    def write(self, data):
        self.encoder.write(data)
        self.encoder.flush()


def as_js_object(dict_):
    obj = Object.create(None)
    for k, v in dict_.items():
        obj[k] = v
    return obj


def get_api_baseurl():
    if location.protocol == "file:":
        __pragma__('js', '{}', '''
        url = new URL(location.href);
        return "http://localhost:"+url.searchParams.get("transmitter");
        ''')
    else:
        return location.origin
