from bigsuds import ServerError
import f5
import f5.util
import re

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

    def __init__(self, name, lb=None, description=None, lbmethod=None, members=None):

        if lb is not None and not isinstance(lb, f5.Lb):
            raise ValueError('lb must be of type lb, not %s' % (type(lb).__name__))

        if lbmethod is not None and lbmethod not in self.__lbmethods:
            raise ValueError(
                    '%s is not a valid value for lbmethod, expecting: %s'
                    % (lbmethod, self.__lbmethods))

        self._lb          = lb
        self._name        = name
        self._description = description
        self._lbmethod    = lbmethod
        self._members     = members

        if lb:
            self._set_wsdl()

    def __repr__(self):
        return "f5.Pool('%s')" % (self._name)

    def __str__(self):
        return self._name

    ###########################################################################
    # Private API
    ###########################################################################
    @staticmethod
    def _get_wsdl(lb):
        return lb._transport.LocalLB.Pool

    def _set_wsdl(self):
            self.__wsdl = self._get_wsdl(self._lb)

    @f5.util.lbwriter
    def _create(self):
        lbmethod = 'LB_METHOD_' + self._lbmethod.upper()

        addrportsq = self._pms_to_addrportsq(self._members)
        self.__wsdl.create_v2([self._name], [lbmethod], [addrportsq])

    @f5.util.lbmethod
    def _get_description(self):
        return self.__wsdl.get_description([self._name])[0]

    @f5.util.lbmethod
    def _get_lb_method(self):
        return self.__wsdl.get_lb_method([self._name])[0]

    @f5.util.lbmethod
    def _get_members(self):
        return self.__wsdl.get_member_v2([self._name])[0]

    @f5.util.lbwriter
    def _set_description(self, value):
        self.__wsdl.set_description([self._name], [value])

    @f5.util.lbwriter
    def _set_lb_method(self, value):
        self.__wsdl.set_lb_method([self._name], [value])

    # Yes, this keeps adding for now.
    @f5.util.lbwriter
    def _add_member(self, value):
        self.__wsdl.add_member_v2([self._name], [value])

    def _addrportsq_to_pms(self, addrportsq):
        pms = []
        for addrport in addrportsq:
            pms.append(f5.PoolMember(addrport['address'], addrport['port'], self, lb=self._lb))

        return pms
 
    def _pms_to_addrportsq(self, pms):
        addrportsq = []
        for pm in pms:
            addrportsq.append({'address': pm._node, 'port': pm._port})

        return addrportsq

    @classmethod
    def _get_list(cls, lb):
        return cls._get_wsdl(lb).get_list()

    @classmethod
    def _get_descriptions(cls, lb, names):
        return cls._get_wsdl(lb).get_description(names)

    @classmethod
    def _get_lbmethods(cls, lb, names):
        return cls._get_wsdl(lb).get_lb_method(names)

    @classmethod
    def _get_memberss(cls, lb, names):
        return cls._get_wsdl(lb).get_member_v2(names)

    @classmethod
    def _get_objects(cls, lb, names, minimal=False):
        """Returns a list of Pool objects from a list of pool names"""
        pools = cls.factory.create(names, lb)

        if not minimal:
            descriptions = cls._get_descriptions(lb, names)
            lbmethods    = cls._get_lbmethods(lb, names)
            members      = cls._get_memberss(lb, names)

        for idx,name in enumerate(names):
            pool = pools[idx]

            if not minimal:
                pool._description = descriptions[idx]
                pool._lbmethod    = lbmethods[idx]
                pool._members     = f5.PoolMember._get_objects(lb, [pool], [members[idx]],
                                        minimal=minimal)

        return pools

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
            self._add_member(self._pms_to_addrportsq(value))

        self._members = value

    ###########################################################################
    # Public API
    ###########################################################################
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

    @f5.util.lbtransaction
    def save(self):
        if not self.exists():
            if self._lbmethod is None or self._members is None:
                raise RuntimeError('lbmethod and members must be set on create')
            self._create()

            if self._description is not None:
                self.description = self._description

Pool.factory = f5.util.CachedFactory(Pool)
