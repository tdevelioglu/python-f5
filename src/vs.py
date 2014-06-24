from bigsuds import ServerError
import f5
import f5.util
import re

class VirtualServer(object):
    __version = 11
    __resource_types = [
            'pool',
            'ip_forwarding',
            'l2_forwarding',
            'reject',
            'fast_l4',
            'fast_http',
            'stateless',
            'dhcp_relay',
            'unknown',
            'internal',
            ]

    _protocols = [
            'any',
            'ipv6',
            'routing',
            'none',
            'fragment',
            'dstopts',
            'tcp',
            'udp',
            'icmp',
            'icmpv6',
            'ospf',
            'sctp',
            'unknown',
            ]

    def __init__(self, name, lb=None, address=None, default_pool=None, enabled=None,
            description=None, port=None, profiles=None, protocol=None, source=None, vstype=None,
            wildmask=None):

        if lb is not None and not isinstance(lb, f5.Lb):
            raise ValueError('lb must be of type lb, not %s' % (type(lb).__name__))

        if protocol is not None and protocol not in self.__protocols:
            raise ValueError(
                    "'%s' is not a valid protocol, expecting: %s"
                    % (protocol, self.__protocols))
        if vstype is not None and vstype not in self.__resource_types:
            raise ValueError(
                    "'%s' is not a valid vstype, expecting: %s"
                    % (vstype, self.__resource_types))

        self._lb           = lb
        self._name         = name
        self._address      = address
        self._default_pool = default_pool
        self._description  = description
        self._enabled      = enabled
        self._port         = port
        self._profiles     = profiles
        self._protocol     = protocol
        self._source       = source
        self._vstype       = vstype
        self._wildmask     = wildmask

        if lb:
            self._set_wsdl()

    def __repr__(self):
        return "f5.Virtualserver('%s')" % (self._name)

    ###########################################################################
    # Private API
    ###########################################################################
    @staticmethod
    def _get_wsdl(lb):
        return lb._transport.LocalLB.VirtualServer

    def _set_wsdl(self):
        self.__wsdl = self._get_wsdl(self._lb)

    @classmethod
    def _get_list(cls, lb):
        return cls._get_wsdl(lb).get_list()

    @classmethod
    def _get_default_pool_names(cls, lb, names):
        return cls._get_wsdl(lb).get_default_pool_name(names)

    @classmethod
    def _get_descriptions(cls, lb, names):
        return cls._get_wsdl(lb).get_description(names)

    @classmethod
    def _get_enabled_states(cls, lb, names):
        return cls._get_wsdl(lb).get_enabled_state(names)

    @classmethod
    def _get_destinations(cls, lb, names):
        return cls._get_wsdl(lb).get_destination(names)

    @classmethod
    def _get_profiles(cls, lb, names):
        return cls._get_wsdl(lb).get_profile(names)

    @classmethod
    def _get_protocols(cls, lb, names):
        return cls._get_wsdl(lb).get_protocol(names)

    @classmethod
    def _get_source_addresses(cls, lb, names):
        return cls._get_wsdl(lb).get_source_address(names)

    @classmethod
    def _get_types(cls, lb, names):
        return cls._get_wsdl(lb).get_type(names)

    @classmethod
    def _get_wildmasks(cls, lb, names):
        return cls._get_wsdl(lb).get_wildmask(names)

    @classmethod
    def _get_objects(cls, lb, names, minimal=False):
        """ Take a list of names and return VirtualServer"""
        objects = []

        if not names:
            return objects

        if not minimal:
            default_pool  = cls._get_default_pool_names(lb, names)
            description   = cls._get_descriptions(lb, names)
            enabled_state = cls._get_enabled_states(lb, names)
            destination   = cls._get_destinations(lb, names)
            profiles      = cls._get_profiles(lb, names)
            protocol      = cls._get_protocols(lb, names)
            source        = cls._get_source_addresses(lb, names)
            vstype        = cls._get_types(lb, names)
            wildmask      = cls._get_wildmasks(lb, names)

        for idx,name in enumerate(names):
            vs = cls.factory.get(name, lb)

            if not minimal:
                vs._address      = destination[idx]['address']
                vs._default_pool = f5.Pool.factory.get(default_pool[idx], lb)
                vs._description  = description[idx]
                vs._enabled      = cls._es_to_bool(enabled_state[idx])
                vs._port         = destination[idx]['port']
                vs._profiles     = profiles[idx]
                vs._protocol     = cls._munge_protocol(protocol[idx])
                vs._source       = source[idx]
                vs._vstype       = cls._munge_vstype(vstype[idx])
                vs._wildmask     = wildmask[idx]

            objects.append(vs)

        return objects

    @f5.util.lbmethod
    def _get_description(self):
        return self.__wsdl.get_description([self._name])[0]

    @f5.util.lbmethod
    def _get_default_pool_name(self):
        return self.__wsdl.get_default_pool_name([self._name])[0]

    @f5.util.lbmethod
    def _get_enabled_state(self):
        return self.__wsdl.get_enabled_state([self._name])[0]

    @f5.util.lbmethod
    def _get_destination(self):
        return self.__wsdl.get_destination_v2([self._name])[0]

    @f5.util.lbmethod
    def _set_destination(self, value):
        self.__wsdl.get_destination_v2([self._name], [value])

    @f5.util.lbmethod
    def _get_profile(self):
        return self.__wsdl.get_profile([self._name])[0]

    @f5.util.lbmethod
    def _get_protocol(self):
        return self.__wsdl.get_protocol([self._name])[0]

    @f5.util.lbmethod
    def _set_protocol(self, value):
        self.__wsdl.set_protocol([self._name], [value])

    @f5.util.lbmethod
    def _get_source_address(self):
        return self.__wsdl.get_source_address([self._name])[0]

    @f5.util.lbmethod
    def _set_source_address(self, value):
        self.__wsdl.set_source_address([self._name], [value])

    @f5.util.lbmethod
    def _get_type(self):
        return self.__wsdl.get_type([self._name])[0]

    @f5.util.lbmethod
    def _set_type(self, value):
        self.__wsdl.set_type([self._name], [value])

    @f5.util.lbmethod
    def _get_wildmask(self):
        return self.__wsdl.get_wildmask([self._name])[0]

    @f5.util.lbwriter
    def _set_description(self, value):
        self.__wsdl.set_description([self._name], [value])

    @f5.util.lbwriter
    def _create(self):
        self.__wsdl._create([self._name])

    @f5.util.lbwriter
    def _delete_virtual_server(self):
        self.__wsdl._delete_virtual_server([self._name])

    @staticmethod
    def _es_to_bool(enabled_state):
        if enabled_state == 'STATE_ENABLED':
            return True
        elif enabled_state == 'STATE_DISABLED':
            return False
        else:
            raise RuntimeError("Unknown enabled_state received for VirtualServer: '%s'" % enabled_state)

    @staticmethod
    def _bool_to_es(_bool):
        if _bool is True:
            return 'STATE_ENABLED'
        elif _bool is False:
            return 'STATE_DISABLED'
        else:
            raise ValueError('enabled must be True or False')

    @classmethod
    def _get(cls, lb, pattern=None, minimal=False):
        names = cls._get_list(lb)
        if pattern is not None:
            if not isinstance(pattern, re._pattern_type):
                pattern = re.compile(pattern)
            names = filter(lambda name: pattern.match(name), names)

        return cls._get_objects(lb, names, minimal)

    @staticmethod
    def _munge_protocol(protocol):
        protocol = protocol.lower()
        if 'protocol_' in protocol:
            return protocol[9:]
        return protocol

    @staticmethod
    def _unmunge_protocol(protocol):
        protocol = protocol.upper()
        if 'PROTOCOL_' not in protocol:
            return 'PROTOCOL_' + protocol
        return protocol

    @staticmethod
    def _munge_vstype(vstype):
        vstype = vstype.lower()
        if 'resource_type_' in vstype:
            return vstype[14:]
        return vstype

    @staticmethod
    def _unmunge_vstype(vstype):
        vstype = vstype.upper()
        if not 'RESOURCE_TYPE_' in vstype:
            return 'RESOURCE_TYPE_' + vstype
        return vstype

    ###########################################################################
    # Properties
    ###########################################################################
    #### lb ####
    @property
    def lb(self):
        return self._lb

    @lb.setter
    @f5.util.updatefactorycache
    def lb(self, value):
        if value is not None and not isinstance(value, f5.Lb):
            raise ValueError('lb must be of type lb, not %s' % (type(value).__name__))
        self._lb = value
        self._set_wsdl()

    #### name ####
    @property
    def name(self):
        return self._name

    @name.setter
    @f5.util.updatefactorycache
    def name(self,value):
        if self._lb:
            raise AttributeError("set attribute name not allowed when linked to lb")
        self._name = name

    #### address ####
    @property
    def address(self):
        if self._lb:
            self._address = self._get_destination()['address']
        return self._address

    @address.setter
    def address(self, value):
        ap = {'address': value, port: self._port}
        if self._lb:
            self._set_destination(ap)
        self._address = value

    #### default_pool ####
    @property
    def default_pool(self):
        if self._lb:
            self._default_pool = self._get_default_pool_name()
        return self._default_pool

    @default_pool.setter
    def default_pool(self, value):
        if isinstance(value, str):
            value = f5.Pool.factory.get(value, self._lb)

        if self._lb:
            self._set_default_pool_name(value.name)
        self._default_pool = value

    #### description ####
    @property
    def description(self):
        if self._lb:
            self._description = self._get_description()
        return self._description

    @description.setter
    def description(self, value):
        if self._lb:
            self._set_description(value)
        self._description = value

    #### enabled ####
    @property
    def enabled(self):
        if self._lb:
            enabled_state = self._get_enabled_state()
            self._enabled = self._es_to_bool(enabled_state)

        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if self._lb:
            self._set_enabled(self._bool_to_es(value))

        self._enabled = value

    #### port ####
    @property
    def port(self):
        if self._lb:
            self._port = self._get_destination()['port']
        return self._port

    @port.setter
    def port(self, value):
        ap = {'address': self._address, 'port': value}
        if self._lb:
            self._set_destination(ap)
        self._port = value

    #### profiles ####
    @property
    def profiles(self):
        if self._lb:
            self._profiles = self._get_profile()
        return self._profiles

    #### protocol ####
    @property
    def protocol(self):
        if self._lb:
            self._protocol = self._munge_protocol(self._get_protocol())
        return self._protocol

    @protocol.setter
    def protocol(self, value):
        if self._lb:
            self._set_protocol(self._unmunge_protocol(value))
        self._protocol = value

    #### source ####
    @property
    def source(self):
        if self._lb:
            self._source = self._get_source_address()
        return self._source

    @source.setter
    def source(self, value):
        if self._lb:
            self._set_source_address(value)
        self._source = value

    #### vstype ####
    @property
    def vstype(self):
        if self._lb:
            self._type = self._munge_vstype(self._get_type())
        return self._type

    @vstype.setter
    def vstype(self, value):
        if value not in self.__resource_types:
            raise ValueError(
                    "'%s' is not a valid value for vstype, expecting: %s"
                    % (value, self.__resource_types))

        if self._lb:
            self._set_type(self._unmunge_vstype(value))

        self._vstype = value

    #### wildmask ####
    @property
    def wildmask(self):
        if self._lb:
            self._wildmask = self._get_wildmask()
        return self._wildmask

    @wildmask.setter
    def wildmask(self, value):
        if self._lb:
            self._set_wildmask(value)
        self._wildmask = value

    ###########################################################################
    # Public API
    ###########################################################################
    def exists(self):
        try:
            self._get_description()
        except ServerError as e:
            if 'was not found' in e.message:
                return False
            else:
                raise
        except:
            raise

        return True

    @f5.util.lbtransaction
    def save(self):
        """Save the virtualserver to the lb"""

        if not self.exists():
            if self._rule_definition is None or self._name is None:
                raise RuntimeError('name and definition must be set on create')
            self._create()
        elif self._definition is not None:
            self.definition = self._definition

        if self._description is not None:
            self.description = self._description
        if self._ignore_verification is not None:
            self.ignore_verification = self._ignore_verification

    def refresh(self):
        """Update all attributes from the lb"""
        self.address
        self.description
        self.default_pool
        self.description
        self.enabled
        self.port
        self.profiles
        self.protocol
        self.source
        self.vstype
        self.wildmask

    def delete(self):
        """Delete the rule from the lb"""
        self._delete_virtual_server()

VirtualServer.factory = f5.util.CachedFactory(VirtualServer)
