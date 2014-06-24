from bigsuds import ServerError
import f5
import f5.util
import re

class Node(object):
    __version = 11

    def __init__(self, name, lb=None, address=None, connection_limit=None, description=None,
            dynamic_ratio=None, enabled=None, rate_limit=None, ratio=None,):

        if lb is not None and not isinstance(lb, f5.Lb):
            raise ValueError('lb must be of type f5.Lb, not %s' % (type(lb).__name__))

        self._lb               = lb
        self._name             = name
        self._address          = address
        self._av_status        = None
        self._connection_limit = connection_limit
        self._description      = description
        self._dynamic_ratio    = dynamic_ratio
        self._enabled          = enabled
        self._rate_limit       = rate_limit
        self._ratio            = ratio
        self._status_descr     = None

        if lb:
            self._set_wsdl()

    def __repr__(self):
        return "f5.Node('%s')" % (self._name)

    ###########################################################################
    # Private API
    ###########################################################################
    @staticmethod
    def _get_wsdl(lb):
        return lb._transport.LocalLB.NodeAddressV2

    def _set_wsdl(self):
            self.__wsdl = self._get_wsdl(self._lb)

    @f5.util.lbwriter
    def _create(self):
        self.__wsdl.create([self._name], [self._address], [self._connection_limit])

    @f5.util.lbmethod
    def _get_address(self):
        return self.__wsdl.get_address([self._name])[0]

    @f5.util.lbmethod
    def _get_connection_limit(self):
        return self.__wsdl.get_connection_limit([self._name])[0]

    @f5.util.lbmethod
    def _get_description(self):
        return self.__wsdl.get_description([self._name])[0]

    @f5.util.lbmethod
    def _get_dynamic_ratio(self):
        return self.__wsdl.get_dynamic_ratio_v2([self._name])[0]

    @f5.util.lbmethod
    def _get_rate_limit(self):
        return self.__wsdl.get_rate_limit([self._name])[0]

    @f5.util.lbmethod
    def _get_ratio(self):
        return self.__wsdl.get_ratio([self._name])[0]

    @f5.util.lbmethod
    def _get_object_status(self):
        return self.__wsdl.get_object_status([self._name])[0]

    @f5.util.lbwriter
    def _set_connection_limit(self, value):
         self.__wsdl.set_connection_limit([self._name], [value])

    @f5.util.lbwriter
    def _set_description(self, value):
         self.__wsdl.set_description([self._name], [value])

    @f5.util.lbwriter
    def _set_dynamic_ratio(self, value):
         self.__wsdl.set_dynamic_ratio_v2([self._name], [value])

    @f5.util.lbwriter
    def _set_rate_limit(self, value):
         self.__wsdl.set_rate_limit([self._name], [value])

    @f5.util.lbwriter
    def _set_ratio(self, value):
         self.__wsdl.set_ratio([self._name], [value])

    @f5.util.lbwriter
    def _set_session_enabled_state(self, value):
        self.__wsdl.set_session_enabled_state([self._name], [value])

    @f5.util.lbwriter
    def _delete_node_address(self):
        self.__wsdl.delete_node_address([self._name])

    @classmethod
    def _get_list(cls, lb):
        return cls._get_wsdl(lb).get_list()

    @classmethod
    def _get_addresses(cls, lb, names):
        return cls._get_wsdl(lb).get_address(names)

    @classmethod
    def _get_connection_limits(cls, lb, names):
        return cls._get_wsdl(lb).get_connection_limit(names)

    @classmethod
    def _get_descriptions(cls, lb, names):
        return cls._get_wsdl(lb).get_description(names)

    @classmethod
    def _get_dynamic_ratios(cls, lb, names):
        return cls._get_wsdl(lb).get_dynamic_ratio(names)

    @classmethod
    def _get_object_statuses(cls, lb, names):
        return cls._get_wsdl(lb).get_object_status(names)

    @classmethod
    def _get_rate_limits(cls, lb, names):
        return cls._get_wsdl(lb).get_rate_limit(names)

    @classmethod
    def _get_ratios(cls, lb, names):
        return cls._get_wsdl(lb).get_ratio(names)

    @staticmethod
    def _enabled_status_to_bool(enabled_status):
        if enabled_status == 'ENABLED_STATUS_ENABLED':
            return True
        elif enabled_status == 'ENABLED_STATUS_DISABLED':
            return False
        else:
            raise RuntimeError("Unknown enabled_status received for Node: '%s'" % enabled_status)

    @staticmethod
    def _bool_to_enabled_status(_bool):
        if _bool == True:
            return 'STATE_ENABLED'
        elif _bool == False:
            return 'STATE_DISABLED'
        else:
            raise ValueError('enabled must be True or False')

    # Get last part of availability_status
    @staticmethod
    def _get_av_status_short(av_status):
        return av_status[20:]

    @classmethod
    def _get_objects(cls, lb, names, minimal=False):
        """Returns a list of node objects from a list of node names"""
        objects = []

        if not names:
            return objects

        if not minimal:
            address          = cls._get_addresses(lb, names)
            connection_limit = cls._get_connection_limits(lb, names)
            object_status    = cls._get_object_statuses(lb, names)
            description      = cls._get_descriptions(lb, names)
            dynamic_ratio    = cls._get_dynamic_ratios(lb, names)
            rate_limit       = cls._get_rate_limits(lb, names)
            ratio            = cls._get_ratios(lb, names)

        for idx,name in enumerate(names):
            node = cls.factory.get(name, lb)

            if not minimal:
                node._address          = address[idx]
                node._av_status        = cls._get_av_status_short(
                        object_status[idx]['availability_status'])
                node._connection_limit = connection_limit[idx]
                node._enabled          = cls._enabled_status_to_bool(
                        object_status[idx]['enabled_status'])
                node._description      = description[idx]
                node._dynamic_ratio    = dynamic_ratio[idx]
                node._rate_limit       = rate_limit[idx]
                node._ratio            = ratio[idx]
                node._status_descr     = object_status[idx]['status_description']

            objects.append(node)

        return objects

    @classmethod
    def _get(cls, lb, pattern=None, minimal=False):
        names = cls._get_list(lb)
        if pattern is not None:
            if not isinstance(pattern, re._pattern_type):
                pattern = re.compile(pattern)
            names = filter(lambda name: pattern.match(name), names)

        return cls._get_objects(lb, names, minimal)

    ###########################################################################
    # Properties
    ###########################################################################
    #### name ####
    @property
    def name(self):
        return self._name

    @name.setter
    @f5.util.updatefactorycache
    def name(self, value):
        if self._lb:
            raise AttributeError("set attribute name not allowed when linked to lb")
        self._name = name

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

    #### address ####
    @property
    def address(self):
        if self._lb:
            self._address = self._get_address()
        return self._address

    @address.setter
    def address(self, value):
        if self._lb:
            # set lb=None if you want to set this, or set _address directly
            raise AttributeError("set attribute address not allowed when linked to lb")

        self._address = value

    #### av_status ####
    @property
    def av_status(self):
        if self._lb:
            self._status_descr = self._get_av_status_short(self._get_object_status()['availability_status'])
        return self._status_descr

    #### connection_limit ####
    @property
    def connection_limit(self):
        if self._lb:
            self._connection_limit = self._get_connection_limit()
        return self._connection_limit

    @connection_limit.setter
    def connection_limit(self, value):
        if self._lb:
            self._set_connection_limit(value)

        self._connection_limit = value

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

    #### dynamic_ratio ####
    @property
    def dynamic_ratio(self):
        if self._lb:
            self._dynamic_ratio = self._get_dynamic_ratio()
        return self._dynamic_ratio

    @dynamic_ratio.setter
    def dynamic_ratio(self, value):
        if self._lb:
            self._set_dynamic_ratio(value)

        self._dynamic_ratio = value

    #### enabled ####
    @property
    def enabled(self):
        if self._lb:
            enabled_status = self._get_object_status()['enabled_status']
            self._enabled = self._enabled_status_to_bool(enabled_status)

        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if self._lb:
            enabled_status = self._bool_to_enabled_status(value)
            self._set_session_enabled_state(enabled_status)

        self._enabled = value

    #### rate_limit ####
    @property
    def rate_limit(self):
        if self._lb:
            self._rate_limit = self._get_rate_limit()
        return self._rate_limit

    @rate_limit.setter
    def rate_limit(self, value):
        if self._lb:
            self._set_rate_limit(value)

        self._rate_limit = value

    #### ratio ####
    @property
    def ratio(self):
        if self._lb:
            self._ratio = self._get_ratio()
        return self._ratio

    @ratio.setter
    def ratio(self, value):
        if self._lb:
            self._set_ratio(value)

        self._ratio = value

    #### status_descr ####
    @property
    def status_descr(self):
        if self._lb:
            self._status_descr = self._get_object_status()['status_description']
        return self._status_descr

    ###########################################################################
    # Public API
    ###########################################################################
    def exists(self):
        try:
            self._get_address()
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
        """Save the node to the lb"""
        if not self.exists():
            if self._address is None or self._connection_limit is None:
                raise RuntimeError('address and connection_limit must be set on create')
            self._create()
        elif self._connection_limit is not None:
            self.connection_limit = self._connection_limit

        if self._description is not None:
            self.description = self._description
        if self._dynamic_ratio is not None:
            self.dynamic_ratio = self._dynamic_ratio
        if self._enabled is not None:
            self.enabled = self._enabled
        if self._rate_limit is not None:
            self.rate_limit = self._rate_limit
        if self._ratio is not None:
            self.ratio = self._ratio

    def refresh(self):
        """Update all attributes from the lb"""
        self.address
        self.av_status
        self.connection_limit
        self.description
        self.dynamic_ratio
        self.enabled
        self.rate_limit
        self.ratio
        self.status_descr

    def delete(self):
        """Delete the node from the lb"""
        self._delete_node_address()

Node.factory = f5.util.CachedFactory(Node)
