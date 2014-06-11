from bigsuds import ServerError
import f5
import f5.util

class Poolmember(object):
    __version = 11

    def __init__(self, node, port, pool, connection_limit=None, description=None,
            dynamic_ratio=None, enabled=None, priority=None, rate_limit=None, ratio=None, lb=None):

        if lb is not None and not isinstance(lb, f5.Lb):
            raise ValueError('lb must be of type lb, not %s' % (type(lb).__name__))

        if isinstance(node, str):
            node = f5.Node(name=node, lb=lb)

        if isinstance(pool, str):
            pool = f5.Pool(name=pool, lb=lb)

        self._lb               = lb
        self._node             = node
        self._pool             = pool
        self._port             = port
        self._address          = node._address
        self._connection_limit = connection_limit
        self._description      = description
        self._dynamic_ratio    = dynamic_ratio
        self._enabled          = enabled
        self._priority         = priority
        self._rate_limit       = rate_limit
        self._ratio            = ratio

        if self._lb:
            self._set_wsdl()

    def _set_wsdl(self):
            self.__wsdl = self._lb._transport.LocalLB.Pool

    def __repr__(self):
        return "f5.poolmember('%s', %s, '%s')" % (self._node, self._port, self._pool)

    @f5.util.lbmethod
    def _get_addrport(self):
        return {'address': self._node.name, 'port': self._port}

    @f5.util.lbmethod
    def _get_address(self):
        return self.__wsdl.get_member_address([self._pool.name], [[self._get_addrport()]])[0][0]

    @f5.util.lbmethod
    def _get_connection_limit(self):
        return self.__wsdl.get_member_connection_limit([self._pool.name], [[self._get_addrport()]])[0][0]

    @f5.util.lbmethod
    def _get_description(self):
        return self.__wsdl.get_member_description([self._pool.name], [[self._get_addrport()]])[0][0]

    @f5.util.lbmethod
    def _get_dynamic_ratio(self):
        return self.__wsdl.get_member_dynamic_ratio([self._pool.name], [[self._get_addrport()]])[0][0]

    @f5.util.lbmethod
    def _get_priority(self):
        return self.__wsdl.get_member_priority([self._pool.name], [[self._get_addrport()]])[0][0]

    @f5.util.lbmethod
    def _get_rate_limit(self):
        return self.__wsdl.get_member_rate_limit([self._pool.name], [[self._get_addrport()]])[0][0]

    @f5.util.lbmethod
    def _get_ratio(self):
        return self.__wsdl.get_member_ratio([self._pool.name], [[self._get_addrport()]])[0][0]

    @f5.util.lbmethod
    def _get_object_status(self):
        return self.__wsdl.get_member_object_status([self._pool.name], [[self._get_addrport()]])[0][0]

    @f5.util.lbwriter
    def _set_description(self, value):
        self.__wsdl.set_member_description([self._pool.name], [[self._get_addrport()]], [[value]])

    @f5.util.lbwriter
    def _set_connection_limit(self, value):
        self.__wsdl.set_member_connection_limit([self._pool.name], [[self._get_addrport()]], [[value]])

    @f5.util.lbwriter
    def _set_dynamic_ratio(self, value):
        self.__wsdl.set_member_dynamic_ratio([self._pool.name], [[self._get_addrport()]], [[value]])

    @f5.util.lbwriter
    def _set_priority(self, value):
        self.__wsdl.set_member_priority([self._pool.name], [[self._get_addrport()]], [[value]])

    @f5.util.lbwriter
    def _set_rate_limit(self, value):
        self.__wsdl.set_member_rate_limit([self._pool.name], [[self._get_addrport()]], [[value]])

    @f5.util.lbwriter
    def _set_ratio(self, value):
        self.__wsdl.set_member_ratio([self._pool.name], [[self._get_addrport()]], [[value]])

    @f5.util.lbwriter
    def _set_session_enabled_state(self, value):
        self.__wsdl.set_member_session_enabled_state([self._pool.name], [[self._get_addrport()]], [[value]])

    @f5.util.lbwriter
    def _create(self):
        self.__wsdl.add_member_v2([self._pool.name], [[self._get_addrport()]])

    @f5.util.lbwriter
    def _remove(self):
        self.__wsdl.remove_member_v2([self._pool.name], [[self._get_addrport()]])

    ###########################################################################
    # Properties
    ###########################################################################

    #### lb ####
    @property
    def lb(self):
        return self._lb

    @lb.setter
    def lb(self, value):
        if value is not None and not isinstance(value, f5.Lb):
            raise ValueError('lb must be of type lb, not %s' % (type(value).__name__))

        self._lb = value
        self._set_wsdl()

        # Also update the node's lb <- not sure (yet) if this is the right thing
        self._node.lb = value

    #### address ####
    @property
    def address(self):
        if self._lb:
            self._address = self._get_address()
        return self._address

    #### node ####
    @property
    def node(self):
       return self._node
    
    @node.setter
    def node(self, value):
        if self._lb:
            raise AttributeError("set attribute node not allowed when linked to lb")

        if isinstance(value, str):
            value = f5.Node(name=value, lb=self._lb)

        self._node = value

    #### port ####
    @property
    def port(self):
       return self._port
    
    @port.setter
    def port(self, value):
        if self._lb:
            raise AttributeError("set attribute port not allowed when linked to lb")

        self._port = value

    #### pool ####
    @property
    def pool(self):
       return self._pool
    
    @pool.setter
    def pool(self, value):
        if self._lb:
            raise AttributeError("set attribute pool not allowed when linked to lb")

        self._pool = value

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

    #### priority ####
    @property
    def priority(self):
       if self._lb:
           self._priority = self._get_priority()

       return self._priority

    @priority.setter
    def priority(self, value):
        if self._lb:
            self._set_priority(value)
        self._priority = value

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

    #### enabled ####
    @property
    def enabled(self):
        if self._lb:
            enabled_status = self._get_object_status()['enabled_status']
            if enabled_status == 'ENABLED_STATUS_ENABLED':
                self._enabled = True
            elif enabled_status == 'ENABLED_STATUS_DISABLED':
                self._enabled = False
            else:
                raise RuntimeError('Unknown enabled_status %s received for poolmember', enabled_status)

        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if value == True:
            enabled_status = 'STATE_ENABLED'
        elif value == False:
            enabled_status = 'STATE_DISABLED'
        else:
            raise ValueError('enabled must be either True or False')

        if self._lb:
            self._set_session_enabled_state(enabled_status)

        self._enabled = value

    ###########################################################################
    # Public API
    ###########################################################################
    @f5.util.lbtransaction
    def save(self):
        """Save the poolmember to the lb"""
        if not self.exists():
            self._create()

        if self._connection_limit is not None:
            self.connection_limit = self._connection_limit
        if self._description is not None:
            self.description = self._description
        if self._dynamic_ratio is not None:
            self.dynamic_ratio = self._dynamic_ratio
        if self._enabled is not None:
            self.enabled = self._enabled
        if self._priority is not None:
            self.priority = self._rate_limit
        if self._rate_limit is not None:
            self.rate_limit = self._rate_limit
        if self._ratio is not None:
            self.ratio = self._ratio

    def delete(self):
        """Delete the poolmember from the lb"""
        self._remove()

    def exists(self):
        """Check if poolmember exists on the lb"""
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

    def refresh(self):
        """Fetch all attributes from the lb"""
        self.address
        self.connection_limit
        self.description
        self.dynamic_ratio
        self.enabled
        self.priority
        self.rate_limit
        self.ratio
