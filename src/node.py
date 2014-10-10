from bigsuds import ServerError
import f5
import f5.util
import re

def enabled_bool(enabled_statuses):
    """Switch from enabled_status to bool"""
    return [True if s == 'ENABLED_STATUS_ENABLED' else False for s in enabled_statuses]


def bool_enabled(bools):
    """Switch from bool to enabled_status"""
    return ['STATE_ENABLED' if b else 'STATE_DISABLED' for b in bools]


# Truncate availability_status
def munge_av_status(av_statuses):
    return [a[20:] for a in av_statuses]


class Node(object):
    __version = 11
    __wsdl = 'LocalLB.NodeAddressV2'

    def __init__(self, name, lb=None, address=None, connection_limit=None, description=None,
            dynamic_ratio=None, enabled=None, rate_limit=None, ratio=None, fromdict=None):

        self._lb = lb

        if fromdict is not None:
            if lb is not None:
                self.dictionary = fromdict
            else:
                self._dictionary = fromdict
        else:
            self.__name            = name
            self._address          = address
            self._av_status        = None
            self._connection_limit = connection_limit
            self._description      = description
            self._dynamic_ratio    = dynamic_ratio
            self._enabled          = enabled
            self._rate_limit       = rate_limit
            self._ratio            = ratio
            self._status_descr     = None

        self._lbcall = self.__lbcall

    def __repr__(self):
        return "f5.Node('%s')" % (self.name)

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
        self.__name = value

    #### ADDRESS ####
    @property
    def address(self):
        self._address = self._lbcall('get_address', [self.name])[0]
        return self._address

    #### AV_STATUS ####
    @property
    def av_status(self):
        self._av_status = munge_av_status(
                [s['availability_status'] for s in self._lbcall('get_object_status', [self.name])])[0]
        return self._av_status

    #### CONNECTION_LIMIT ####
    @property
    def connection_limit(self):
        self._connection_limit = self._lbcall('get_connection_limit', [self.name])[0]
        return self._connection_limit

    @connection_limit.setter
    @f5.util.lbwriter2
    def connection_limit(self, value):
        self._lbcall('set_connection_limit', [self.name], [value])
        self._connection_limit = value

    #### DESCRIPTION ####
    @property
    def description(self):
        self._description = self._lbcall('get_description', [self._name])[0]
        return self._description

    @description.setter
    @f5.util.lbwriter2
    def description(self, value):
        self._lbcall('set_description', [self.name], [value])
        self._description = value

    #### DYNAMIC_RATIO ####
    @property
    def dynamic_ratio(self):
        self._dynamic_ratio = self._lbcall('get_dynamic_ratio_v2', [self.name])[0]
        return self._dynamic_ratio

    @dynamic_ratio.setter
    @f5.util.lbwriter2
    def dynamic_ratio(self, value):
        self._lbcall('set_dynamic_ratio_v2', [self.name], [value])
        self._description = value

    #### ENABLED ####
    # We do a little fancy stuff here, munging the internal (f5) enabled status to a bool and back.
    @property
    def enabled(self):
        self._enabled = enabled_bool([s['enabled_status'] for s in self._lbcall('get_object_status', [self.name])])[0]
        return self._enabled

    @enabled.setter
    @f5.util.lbwriter2
    def enabled(self, value):
        self._lbcall('set_session_enabled_state', [self.name], bool_enabled([value]))
        self._enabled = value

    #### RATE_LIMIT ####
    @property
    def rate_limit(self):
        self._rate_limit = self._lbcall('get_rate_limit', [self.name])[0]
        return self._rate_limit

    @rate_limit.setter
    @f5.util.lbwriter2
    def rate_limit(self, value):
        self._lbcall('set_rate_limit', [self.name], [value])
        self._rate_limit = value

    #### RATIO ####
    @property
    def ratio(self):
        self._ratio = self._lbcall('get_ratio', [self.name])[0]
        return self._ratio

    @ratio.setter
    @f5.util.lbwriter2
    def ratio(self, value):
        self._lbcall('set_ratio', [self.name], [value])
        self._ratio = value

    #### STATUS_DESCR ####
    @property
    def status_descr(self):
        self._status_descr = self._lbcall('get_object_status', [self.name])[0]['status_description']
        return self._status_descr

    @property
    def dictionary(self):
        d = {}

        d['lb']               = self.lb
        d['name']             = self.name
        d['address']          = self.address
        d['av_status']        = self.av_status
        d['connection_limit'] = self.connection_limit
        d['description']      = self.description
        d['dynamic_ratio']    = self.dynamic_ratio
        d['enabled']          = self.enabled
        d['rate_limit']       = self.rate_limit
        d['ratio']            = self.ratio
        d['status_descr']     = self.status_descr

        return d

    @property
    def _dictionary(self):
        d = {}

        d['lb']               = self._lb
        d['name']             = self._name
        d['address']          = self._address
        d['av_status']        = self._av_status
        d['connection_limit'] = self._connection_limit
        d['description']      = self._description
        d['dynamic_ratio']    = self._dynamic_ratio
        d['enabled']          = self._enabled
        d['rate_limit']       = self._rate_limit
        d['ratio']            = self._ratio
        d['status_descr']     = self._status_descr

        return d

    @dictionary.setter
    @f5.util.lbwriter2
    def dictionary(self, d):
        self._name            = d['name']
        self._address         = d['address']
        self._av_status       = d['av_status']
        self.connection_limit = d['connection_limit']
        self.description      = d['description']
        self.dynamic_ratio    = d['dynamic_ratio']
        self.enabled          = d['enabled']
        self.rate_limit       = d['rate_limit']
        self.ratio            = d['ratio']
        self._status_descr    = d['status_descr']

    @_dictionary.setter
    def _dictionary(self, d):
        self._name             = d['name']
        self._address          = d['address']
        self._av_status        = d['av_status']
        self._connection_limit = d['connection_limit']
        self._description      = d['description']
        self._dynamic_ratio    = d['dynamic_ratio']
        self._enabled          = d['enabled']
        self._rate_limit       = d['rate_limit']
        self._ratio            = d['ratio']
        self._status_descr     = d['status_descr']

    ###########################################################################
    # Private API
    ###########################################################################
    @classmethod
    def _get_objects(cls, lb, names, minimal=False):
        """Returns a list of node objects from a list of node names"""

        if not names:
            return []

        if not minimal:
            address          = cls._lbcall(lb, 'get_address', names)
            connection_limit = cls._lbcall(lb, 'get_connection_limit', names)
            object_status    = cls._lbcall(lb, 'get_object_status', names)
            av_status        = munge_av_status([s['availability_status'] for s in object_status])
            enabled          = enabled_bool([s['enabled_status'] for s in object_status])
            description      = cls._lbcall(lb, 'get_description', names)
            dynamic_ratio    = cls._lbcall(lb, 'get_dynamic_ratio', names)
            rate_limit       = cls._lbcall(lb, 'get_rate_limit', names)
            ratio            = cls._lbcall(lb, 'get_ratio', names)

        nodes = cls.factory.create(names, lb)
        if not minimal:
            for idx, node in enumerate(nodes):
                node._address          = address[idx]
                node._av_status        = av_status[idx]
                node._connection_limit = connection_limit[idx]
                node._enabled          = enabled[idx]
                node._description      = description[idx]
                node._dynamic_ratio    = dynamic_ratio[idx]
                node._rate_limit       = rate_limit[idx]
                node._ratio            = ratio[idx]
                node._status_descr     = object_status[idx]['status_description']

        return nodes

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
    def exists(self):
        try:
            self._lbcall('get_address', [self._name])
        except ServerError as e:
            if 'was not found' in str(e):
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
            self._lbcall('create', [self._name], [self._address], [self._connection_limit])
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

    @f5.util.lbwriter2
    def delete(self, force=False):
        """Delete the node from the lb"""
        if force is True:
            # Delete all associated poolmembers
            # Replace this with a PoolMemberList when ready.
            for pm in self.lb.pms_get(pattern='^%s:[0-9]+$' % self.name, minimal=True):
                pm.delete()
        self._lbcall('delete_node_address', [self._name])

Node.factory = f5.util.CachedFactory(Node)


class NodeList(list):
    def __init__(self, lb=None, pattern=None, partition='/', minimal=False, fromdict=None):
        self._lb = lb
        self._minimal   = minimal
        self._partition = partition
        self._pattern   = pattern

        if fromdict is not None:
            self.dictionary = fromdict
        elif lb is not None:
            self.refresh()

    @f5.util.restore_session_values
    def refresh(self):
        self.lb.active_folder = self._partition
        if self._partition == '/':
            self.lb.recursive_query = True

        nodes = Node._get(self._lb, self._pattern, self._minimal)
        del self[:]
        self.extend(nodes)

    @f5.util.lbtransaction
    def sync(self, create=False):
        if create is True:
            self._lbcall('create', self.names, self._getattr('_address'),
                    self._getattr('_connection_limit'))
        else:
            self.connection_limit = self._getattr('_connection_limit')

        self.description   = self._getattr('_description')
        self.dynamic_ratio = self._getattr('_dynamic_ratio')
        self.enabled       = bool_enabled(self._getattr('_enabled'))
        self.rate_limit    = self._getattr('_rate_limit')
        self.ratio         = self._getattr('_ratio')

    def _lbcall(self, call, *args, **kwargs):
        return Node._lbcall(self._lb, call, *args, **kwargs)

    def _setattr(self, attr, values):
        """Sets an attribute on all objects in list"""
        if len(values) is not len(self):
            raise ValueError('value must be of same length as list')

        for idx,node in enumerate(self):
            setattr(node, attr, values[idx])

    def _getattr(self, attr):
        return [getattr(node, attr) for node in self]

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

    #### ADDRESS ####
    @property
    def address(self):
        values = self._lbcall('get_address', self.names)
        self._setattr('_address', values)
        return values

    @property
    def _address(self):
        return self._getattr('_address')

    @_address.setter
    @f5.util.multisetter
    def _address(self, values):
        self._setattr('_address',  values)

    #### AV_STATUS ####
    @property
    def av_status(self):
        values = munge_av_status(
                [s['availability_status'] for s in self._lbcall('get_object_status', self.names)])
        self._setattr('_av_status', values)
        return values

    @property
    def _av_status(self):
        return self._getattr('_av_status')

    ### CONNECTION_LIMIT ###
    @property
    def connection_limit(self):
        values = self._lbcall('get_connection_limit', self.names)
        self._setattr('_connection_limit',  values)
        return values

    @connection_limit.setter
    @f5.util.multisetter
    @f5.util.lbwriter2
    def connection_limit(self, values):
        self._lbcall('set_connection_limit', self.names, values)
        self._setattr('_connection_limit', values)

    @property
    def _connection_limit(self):
        return self._getattr('_connection_limit')

    @_connection_limit.setter
    @f5.util.multisetter
    def _connection_limit(self, values):
        return self._setattr('_connection_limit', values)

    ### DESCRIPTION ###
    @property
    def description(self):
        values = self._lbcall('get_description', self.names)
        self._setattr('_description', values)
        return values

    @description.setter
    @f5.util.multisetter
    @f5.util.lbwriter2
    def description(self, values):
        self._lbcall('set_description', self.names, values)
        self._setattr('_description', values)

    @property
    def _description(self):
        return self._getattr('_description')

    @_description.setter
    @f5.util.multisetter
    def _description(self, values):
        return self._setattr('_description', values)

    ### DYNAMIC_RATIO ###
    @property
    def dynamic_ratio(self):
        values = self._lbcall('get_dynamic_ratio', self.names)
        self._setattr('_dynamic_ratio', values)
        return values

    @dynamic_ratio.setter
    @f5.util.multisetter
    @f5.util.lbwriter2
    def dynamic_ratio(self, values):
        self._lbcall('set_dynamic_ratio', self.names, values)
        self._setattr('_dynamic_ratio', values)

    @property
    def _dynamic_ratio(self):
        return self._getattr('_dynamic_ratio')

    @_dynamic_ratio.setter
    @f5.util.multisetter
    def _dynamic_ratio(self, values):
        return self._setattr('_dynamic_ratio', values)

    ### ENABLED ###
    @property
    def enabled(self):
        values = enabled_bool([s['enabled_status'] for s in self._lbcall('get_object_status', self.names)])
        self._setattr('_enabled', values)
        return values
     
    @enabled.setter
    @f5.util.multisetter
    @f5.util.lbwriter2
    def enabled(self, values):
        self._lbcall('set_session_enabled_state', self.names, bool_enabled(values))
        self._setattr('_enabled', values)

    @property
    def _enabled(self):
        return self._getattr('_enabled')

    @_enabled.setter
    @f5.util.multisetter
    def _enabled(self, values):
        return self._setattr('_enabled', values)

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
    @f5.util.multisetter
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
    @f5.util.lbwriter2
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
    @f5.util.lbwriter2
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
