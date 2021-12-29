# __pragma__("skip")
def __pragma__(*args): pass
# __pragma__("noskip")


def create_worker():
    __pragma__('js', '{}', '''
        return new Worker(
            new URL(location.origin + "/socket.js"),
            {type: "classic"});
    ''')
