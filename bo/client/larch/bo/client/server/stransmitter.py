from .transmitter import Transmitter


# __pragma__("skip")
class Mock:
    pass


window = Mock()
def __pragma__(*args): pass
def create_worker(): return Mock()
# __pragma__("noskip")


__pragma__('js', '{}', '''
function create_worker() {
    return new Worker(
        new URL(location.origin + "/socket.js"),
        {type: "classic"});
}
''')

window.transmitter = Transmitter(create_worker())
