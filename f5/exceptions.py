import re

class BigSudsExceptionParser(object):
    """ This class parses the exception from bigsuds and makes possible
        to read it in a decent way
    """
    _instance = None
    _caught = None
    _exception = None
    _primary_error_code = None
    _secondary_error_code = None
    _error_string = None
    _parser = re.compile(r"^(?P<ins>\w+) raised fault: '(?P<cg>.+)\n"
        "Exception: (?P<ex>.+)\n\s+primary_error_code.+: (?P<pec>.+)\n"
        "\s+secondary_error_code.+: (?P<sec>.+)\n"
        "\s+error_string.+: (?P<es>.+)'", re.MULTILINE)

    # Example of traceback message
    #
    # Server raised fault: 'Exception caught in LocalLB::urn:iControl:LocalLB/Pool::get_active_member_count()
    # Exception: Common::OperationFailed
    #     primary_error_code   : 16908342 (0x01020036)
    #     secondary_error_code : 0
    #     error_string         : 01020036:3: The requested pool (/EXAMPLE/www.example.com) was not found.'

    def __init__(self, _exception):
        try:
            data = self._parser.match(_exception.message).groupdict()
        except AttributeError:
            raise _exception

        self._instance = data['ins']
        self._caught = data['cg']
        self._exception = data['ex']
        self._primary_error_code = data['pec']
        self._secondary_error_code = data['sec']
        self._error_string = data['es']

    @property
    def caught(self):
        return self._caught

    @property
    def error_string(self):
        return self._error_string

    @property
    def exception(self):
        return self._exception

    @property
    def instance(self):
        return self._instance

    @property
    def primary_error_code(self):
        return self._primary_error_code

    @property
    def secondary_error_code(self):
        return self._secondary_error_code


class NodeNotFound(Exception):
    pass


class PoolNotFound(Exception):
    pass


class PoolMemberNotFound(Exception):
    pass


class RuleNotFound(Exception):
    pass


class UnsupportedF5Version(Exception):
    def __init__(self, message, version):
        Exception.__init__(self, message)
        self.version = version


class VirtualServerNotFound(Exception):
    pass



