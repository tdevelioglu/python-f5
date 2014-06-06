from bigsuds import ServerError
import f5
import f5.util

class Pool(object):
    __version = 11
    __lbmethods = [
            'round_robin',
            'ratio_member',
            'least_connection_member',
            'observed_member',
            'predictive_member',
            'ratio_node_address',
            'least_connection_node_address',
            'fastest_node_address',
            'observed_node_address',
            'predictive_node_address',
            'dynamic_ratio',
            'fastest_app_response',
            'least_sessions',
            'dynamic_ratio_member',
            'l3_addr',
            'unknown',
            'weighted_least_connection_member',
            'weighted_least_connection_node_address',
            'ratio_session',
            'ratio_least_connection_member',
            'ratio_least_connection_node_address'
            ]

    def __init__(self, name, description=None, lbmethod=None, members=None, lb=None):

        if lb is not None and not isinstance(lb, f5.Lb):
            raise ValueError('lb must be of type lb, not %s' % (type(lb).__name__))

        if lbmethod is not None and lbmethod not in self.__lbmethods:
            raise ValueError('%s is not a valid value for lbmethod, expecting: %s' % (lbmethod, self.__lbmethods))

        self._lb          = lb
        self._name        = name
        self._description = description
        self._lbmethod    = lbmethod
        self._members     = members

        if lb:
            self._set_wsdl()

    def _set_wsdl(self):
            self.__wsdl = self._lb._transport.LocalLB.Pool

    def __repr__(self):
        return "f5.pool('%s')" % (self._name)

    def _create(self):
        lbmethod = 'LB_METHOD_' + self._lbmethod.upper()

        addrportsq = self._pms_to_addrportsq(self._members)
        self.__wsdl.create_v2([self._name], [lbmethod], [addrportsq])

    def _get_description(self):
        return self.__wsdl.get_description([self._name])[0]

    def _get_lb_method(self):
        return self.__wsdl.get_lb_method([self._name])[0]

    def _get_members(self):
        return self.__wsdl.get_member_v2([self._name])[0]

    def _set_description(self, value):
        self.__wsdl.set_description([self._name], [value])

    def _set_lb_method(self, value):
        self.__wsdl.set_lb_method([self._name], [value])

    def _set_members(self, value):
        self.__wsdl.set_member_v2([self._name], [value])

    def _addrportsq_to_pms(self, addrportsq):
        pms = []
        for addrport in addrportsq:
            pms.append(f5.Poolmember(addrport['address'], addrport['port'], self, lb=self._lb))

        return pms
 
    def _pms_to_addrportsq(self, pms):
        addrportsq = []
        for pm in pms:
            addrportsq.append({'address': pm._node, 'port': pm._port})

        return addrportsq

    ###########################################################################
    # Properties
    ###########################################################################

    #### name ####
    @property
    def name(self):
        return self._name

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

    #### lbmethod ####
    @property
    def lbmethod(self):
        if self._lb:
            self._lbmethod = self._get_lb_method()[10:].lower()
        return self._lbmethod

    @lbmethod.setter
    def lbmethod(self, value):
        if not value in self.__lbmethods:
            raise ValueError('%s is not a valid value for lbmethod, expecting: %s' % (value, self.__lbmethods))

        if self._lb:
            lbmethod = 'LB_METHOD_' + value.upper()
            self._set_lb_method(lbmethod)

        self._lbmethod = value

    #### members ####
    @property
    def members(self):
        if self._lb:
            self._members = self._addrportsq_to_pms(self._get_members())
        return self._members


    @members.setter
    def members(self, value):
        if self._lb:
            self._set_members(self._pms_to_addrportsq(value))

        self._members = value

    ###########################################################################
    # Public API
    ###########################################################################
    @f5.util.lbmethod
    def refresh(self):
        """Fetch all attributes from the lb"""
        self.description
        self.lbmethod
        self.members

    def exists(self):
        try:
            self._get_lb_method()
        except ServerError as e:
            if 'was not found' in e.message:
                return False
            else:
                raise
        except:
            raise

        return True

    @f5.util.lbmethod
    @f5.util.lbrestore_session_values
    @f5.util.lbwriter
    @f5.util.lbtransaction
    def save(self):
        if not self.exists():
            if self._lbmethod is None or self._members is None:
                raise RuntimeError('lbmethod and members must be set on create')
            self._create()

            if self._description is not None:
                self.description = self._description

