import f5
import f5.util
import re

from bigsuds import ServerError

# Convert PoolMember objects into a list of address, port dictionaries
def pms_to_addrportsq(poolmembers):
    """ Converts PoolMembers into a list of address, port dictionaries """
    return [{'address': p._node.name, 'port': p._port} for p in poolmembers]


# Truncate lbmethod
def munge_lbmethod(lbmethods):
    return [l[10:].lower() for l in lbmethods]


# Un-truncate lbmethod
def unmunge_lbmethod(lbmethods):
    return['LB_METHOD_' + l.upper() for l in lbmethods]


class Pool(object):
    __version = 11
    __wsdl = 'LocalLB.Pool'

    def __init__(self, name, lb=None, description=None, lbmethod=None,
            members=None, minimum_active_member=None, minimum_up_member=None,
            slow_ramp_time=None, fromdict=None):

        self._lb = lb

        if fromdict is not None:
            if lb is not None:
                self.dictionary = fromdict
            else:
                self._dictionary = fromdict
        else:
            self.__name                 = name
            self._active_member_count   = None
            self._description           = description
            self._lbmethod              = lbmethod
            self._members               = members
            self._minimum_active_member = minimum_active_member
            self._minimum_up_member     = minimum_up_member
            self._slow_ramp_time        = None
            self._statistics            = None

        self._lbcall = self.__lbcall

    def __repr__(self):
        return "f5.Pool('%s')" % (self._name)

    def __str__(self):
        return self._name

    # This just adds the wsdl to calls to the lb for convenience
    def __lbcall(self, call, *args, **kwargs):
        return self.lb._call(self.__wsdl + '.' + call, *args, **kwargs)

    @classmethod
    def _lbcall(cls, lb, call, *args, **kwargs):
        return lb._call(cls.__wsdl + '.' + call, *args, **kwargs)

    ###########################################################################
    # Properties
    ###########################################################################
    # Asynchronous properties are prefixed with a '_'
    #
    # All properties are fetched directly from the lb, but also stored in local 
    # variables prefixed with an underscore '_' for convenience.
    #
    # If you want to fetch an attribute without calling the lb, get the
    # attribute prefixed with an underscore.

    #### LB ####
    @property
    def lb(self):
        return self._lb

    @lb.setter
    def lb(self, value):
        self.refresh()
        self._lb = value

    #### NAME ####
    @property
    def name(self):
        return self.__name

    @property
    def _name(self):
        return self.__name

    @_name.setter
    @f5.util.updatefactorycache
    def _name(self, value):
        self.__name = name

    #### ACTIVE_MEMBER_COUNT ####
    @property
    def active_member_count(self):
        self._active_member_count = self._lbcall('get_active_member_count', [self._name])[0]
        return self._active_member_count

    #### DESCRIPTION ####
    @property
    def description(self):
        self._description = self._lbcall('get_description', [self._name])[0]
        return self._description

    @description.setter
    @f5.util.lbwriter2
    def description(self, value):
        self._lbcall('set_description', [self._name], [value])
        self._description = value

    #### LBMETHOD ####
    @property
    def lbmethod(self):
        self._lbmethod = munge_lbmethod(self._lbcall('get_lb_method', [self._name]))[0]
        return self._lbmethod

    @lbmethod.setter
    def lbmethod(self, value):
        self._lbcall('set_lb_method', [self._name], unmunge_lbmethod([value]))
        self._lbmethod = value.lower()

    #### MEMBERS ####
    @property
    def members(self):
        self._members = f5.PoolMember._get(self._lb, pools=[self], minimal=True)
        return self._members

    @members.setter
    @f5.util.lbtransaction
    def members(self, value):
        current = self._lbcall('get_member', [self._name])
        should  = pms_to_addrportsq(value)

        self._lbcall('remove_member', [self._name], [current])
        self._lbcall('add_member', [self._name], [should])
        self._members = value

    #### MINIMUM_ACTIVE_MEMBER ####
    @property
    def minimum_active_member(self):
        self._minimum_active_member = self._lbcall(
                'get_minimum_active_member', [self._name])[0]
        return self._minimum_active_member

    @minimum_active_member.setter
    @f5.util.lbwriter2
    def minimum_active_member(self, value):
        self._lbcall('set_minimum_active_member', [self._name], [value])
        self._minimum_active_member = value

    #### MINIMUM_UP_MEMBER ####
    @property
    def minimum_up_member(self):
        self._minimum_up_member = self._lbcall(
                'get_minimum_up_member', [self._name])[0]
        return self._minimum_up_member

    @minimum_up_member.setter
    @f5.util.lbwriter2
    def minimum_up_member(self, value):
        self._lbcall('set_minimum_up_member', [self._name], [value])
        self._minimum_up_member = value

    #### SLOW_RAMP_TIME ####
    @property
    def slow_ramp_time(self):
        self._slow_ramp_time = self._lbcall(
                'get_slow_ramp_time', [self._name])[0]
        return self._slow_ramp_time

    @slow_ramp_time.setter
    @f5.util.lbwriter2
    def slow_ramp_time(self, value):
        self._lbcall('set_slow_ramp_time', [self._name], [value])
        self._slow_ramp_time = value

    #### STATISTICS ####
    @property
    def statistics(self):
        self._statistics = self._lbcall('get_statistics',
                             [self._name])['statistics'][0]
        return self._statistics

    ###########################################################################
    # Private API
    ###########################################################################
    @classmethod
    def _get_objects(cls, lb, names, minimal=False):
        """Returns a list of Pool objects from a list of pool names"""

        if not names:
            return []

        pools = cls.factory.create(names, lb)

        if not minimal:
            active_member_count   = cls._lbcall(lb, 'get_active_member_count',
                                        names)
            description           = cls._lbcall(lb, 'get_description', names)
            lbmethod              = cls._lbcall(lb, 'get_lb_method', names)
            members               = cls._lbcall(lb, 'get_member', names)
            minimum_active_member = cls._lbcall(lb, 'get_minimum_active_member',
                                        names)
            minimum_up_member     = cls._lbcall(lb, 'get_minimum_up_member',
                                        names)
            slow_ramp_time        = cls._lbcall(lb, 'get_slow_ramp_time', names)
            statistics            = cls._lbcall(lb, 'get_statistics', names)

            for idx,pool in enumerate(pools):
                pool._active_member_count   = active_member_count[idx]
                pool._description           = description[idx]
                pool._lbmethod              = lbmethod[idx]
                pool._minimum_active_member = minimum_active_member[idx]
                pool._minimum_up_member     = minimum_up_member[idx]
                pool._slow_ramp_time        = slow_ramp_time[idx]
                pool._statistics            = statistics['statistics'][idx]

                pool._members = f5.PoolMember._get_objects(lb, [pool],
                                    [members[idx]], minimal=True)

        return pools

    @classmethod
    def _get(cls, lb, pattern=None, minimal=False):
        names = cls._lbcall(lb, 'get_list')

        if not names:
            return []

        if pattern is not None:
            if not isinstance(pattern, re._pattern_type):
                pattern = re.compile(pattern)
            names = [name for name in names if pattern.match(name)]

        return cls._get_objects(lb, names, minimal)

    ###########################################################################
    # Public API
    ###########################################################################
    def refresh(self):
        """Fetch all attributes from the lb"""
        self.active_member_count
        self.description
        self.lbmethod
        self.members
        self.minimum_active_member
        self.minimum_up_member
        self.slow_ramp_time
        self.statistics

    def exists(self):
        try:
            self._lbcall('get_description', [self._name])
        except ServerError as e:
            if 'was not found' in str(e):
                return False
            else:
                raise
        except:
            raise

        return True

    def reset_statistics(self):
        self._lbcall('reset_statistics', [self._name])

    @f5.util.lbtransaction
    def save(self):
        if not self.exists():
            if self._lbmethod is None or self._members is None:
                raise RuntimeError('lbmethod and members must be set on create')
            self._lbcall('create_v2', [self._name],
                    [unmunge_lbmethod([self._lbmethod])[0]], [self._members])

            if self._description is not None:
                self.description = self._description

    @f5.util.lbwriter2
    def delete(self):
        """Delete the pool from the lb"""
        self._lbcall('delete_pool', [self._name])

Pool.factory = f5.util.CachedFactory(Pool)


class PoolList(list):
    def __init__(self,
            lb        = None,
            pattern   = None,
            partition = '/',
            fromdict  = None):

        self._lb = lb
        self._partition = partition
        self._pattern   = pattern

        if lb is not None:
            self.refresh()
        else:
            self.dictionary = fromdict

    @f5.util.restore_session_values
    def refresh(self):
        self.lb.active_folder = self._partition
        if self._partition == '/':
            self.lb.recursive_query = True

        pools = Pool._get(self._lb, self._pattern)
        del self[:]
        self.extend(pools)

    @f5.util.lbtransaction
    def sync(self, create=False):
        if create is True:
            self._lbcall('create_v2', [self.names], self._getattr('_lbmethod'),
                    [self._getattr('_members')])
        else:
            self.lbmethod = self._getattr('_lbmethod')
            self.members  = self._getattr('_members')

        self.description = self._getattr('_description')

    def _lbcall(self, call, *args, **kwargs):
        return Pool._lbcall(self._lb, call, *args, **kwargs)

    def _setattr(self, attr, values):
        if len(values) != len(self):
                raise ValueError('value must be of same length as list')

        for idx,pool in enumerate(self):
            setattr(pool, attr, values[idx])

    def _getattr(self, attr):
        return [getattr(pool, attr) for pool in self]

    @property
    def partition(self):
        return self._partition

    @partition.setter
    def partition(self, value):
        self._partition = value
        refresh()

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, value):
        self._pattern =  value
        self.refresh()

    #### DESCRIPTION ####
    @property
    def description(self):
        values = self._lbcall('get_description', self.names)
        self._setattr('_description', values)
        return values

    @description.setter
    @f5.util.multisetter
    def description(self, values):
        self._lbcall('set_description', self.names,  values)
        self._setattr('_description',  values)

    @property
    def _description(self):
        return self._getattr('_description')

    @_description.setter
    @f5.util.multisetter
    def _lbmethod(self, values):
        self._setattr('_description',  values)

    #### LBMETHOD ####
    @property
    def lbmethod(self):
        values = self._lbcall('get_lbmethod', self.names)
        self._setattr('_lbmethod', values)
        return values

    @property
    def _lbmethod(self):
        return self._getattr('_lbmethod')

    @_lbmethod.setter
    @f5.util.multisetter
    def _lbmethod(self, values):
        self._setattr('_lbmethod',  values)

    #### LB ####
    @property
    def lb(self):
        return self._lb

    @lb.setter
    @f5.util.multisetter
    def lb(self, value):
        self._setattr('_lb', value)
        self._lb = value

    #### NAME ####
    @property
    def names(self):
        return self._getattr('name')

    @property
    def _names(self):
        return self._names

    @_names.setter
    def _names(self, values):
        self._setattr('_name', values)

    ### RATE_LIMIT ###
    @property
    def rate_limit(self):
        values = self._lbcall('get_rate_limit', self.names)
        self._setattr('_rate_limit', values)
        return values

    @rate_limit.setter
    @f5.util.multisetter
    def rate_limit(self, values):
        self._lbcall('set_rate_limit', self.names, values)
        self._setattr('_rate_limit', values)

    @property
    def _rate_limit(self):
        return self._getattr('_rate_limit')

    @_rate_limit.setter
    @f5.util.multisetter
    def _rate_limit(self, values):
        return self._setattr('_rate_limit', values)

    ### RATIO ###
    @property
    def ratio(self):
        values = self._lbcall('get_ratio', self.names)
        self._setattr('_ratio', values)
        return values

    @ratio.setter
    @f5.util.multisetter
    def ratio(self, values):
        self._lbcall('set_ratio', self.names, values)
        self._setattr('_ratio', values)

    @property
    def _ratio(self):
        return self._getattr('_ratio')

    @_ratio.setter
    @f5.util.multisetter
    def _ratio(self, values):
        return self._setattr('_ratio', values)

    #### STATUS_DESCR ####
    @property
    def status_descr(self):
        values = [s['status_description'] for s in self._lbcall('get_object_status', self.names)]
        self._setattr('_status_descr', values)
        return values

    @property
    def _status_descr(self):
        return self._getattr('_status_descr')

    #### DICTIONARY ####
    @property
    def dictionary(self):
        d = {}
        d['lb']        = self.lb
        d['partition'] = self.partition
        d['pattern']   = self.pattern

        self.address
        self.av_status
        self.connection_limit
        self.description
        self.dynamic_ratio
        self.enabled
        self.rate_limit
        self.ratio
        self.status_descr

        d['nodes'] =  [node._dictionary for node in self]
        
        return d

    @property
    def _dictionary(self):
        d = {}

        d['lb']        = self.lb
        d['partition'] = self.partition
        d['pattern']   = self.pattern
        # We're in asynchronous mode so we can simply use Node's builtin ._dictionary
        d['nodes']     = [node._dictionary for node in self]

        return d

    @dictionary.setter
    @f5.util.lbtransaction
    def dictionary(self, _dict):
        # Set asynchronous attributes so we don't refresh from lb
        self._lb        = _dict['lb']
        self._partition = _dict['partition']
        self._pattern   = _dict['pattern']

        del self[:]
        self.extend(Node.factory.create([d['name'] for d in _dict['nodes']], self._lb))

        self.connection_limit = [node['connection_limit'] for node in _dict['nodes']]
        self.description      = [node['description'] for node in _dict['nodes']]
        self.dynamic_ratio    = [node['dynamic_ratio'] for node in _dict['nodes']]
        self.enabled          = [node['enabled'] for node in _dict['nodes']]
        self.rate_limit       = [node['rate_limit'] for node in _dict['nodes']]
        self.ratio            = [node['ratio'] for node in _dict['nodes']]

    @_dictionary.setter
    def _dictionary(self, _dict):
        self._lb        = _dict['lb']
        self._partition = _dict['partition']
        self._pattern   = _dict['pattern']

        nodes = Node.factory.create([d['name'] for d in _dict['nodes']], self._lb)
        # We're in asynchronous mode so we can simply use Node's builtin ._dictionary
        for idx, node in enumerate(nodes):
            node._dictionary = _dict['nodes'][idx]

        del self[:]
        self.extend(nodes)
