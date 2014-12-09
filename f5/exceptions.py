class UnsupportedF5Version(Exception):
    def __init__(self, message, version):
        Exception.__init__(self, message)
        self.version = version
