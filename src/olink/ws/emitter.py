
class Emitter:
    def __init__(self):
        self._callbacks = {}

    def on(self, event, callback):
        self._callbacks[event] = callback

    def emit(self, event, *args):
        self._callbacks[event](*args)

    def off(self, event):
        self._callbacks.pop(event)

