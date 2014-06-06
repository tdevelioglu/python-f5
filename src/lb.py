import bigsuds
import re
from bigsuds import ServerError
from copy import copy
from f5.exceptions import UnsupportedF5Version
import f5
import f5.util

###########################################################################
# Decorators
###########################################################################
from functools import wraps

# Restore session attributes to their original values if they were changed
def restore_session_values(func):
    def wrapper(self, *args, **kwargs):
        original_folder          = self._active_folder
        original_recursive_query = self._recursive_query

        func_ret = func(self, *args, **kwargs)

        if self._active_folder != original_folder:
            self.active_folder = original_folder

        if self._recursive_query != original_recursive_query:
            self.recursive_query = original_recursive_query

        return func_ret

    return wrapper

# Enable recursive reading
def recursivereader(func):
    @wraps(func)
    @restore_session_values
    def wrapper(self, *args, **kwargs):

        if self._active_folder != '/':
            self.active_folder = '/'
        if self._recursive_query != True:
            self.recursive_query = True

        return func(self, *args, **kwargs)

    return wrapper

# Set active folder to writable one if it is not
def writer(func):
    @wraps(func)
    @restore_session_values
    def wrapper(self, *args, **kwargs):
        if self._active_folder == '/':
            self.active_folder = '/Common'

            return func(self, *args, **kwargs)

    return wrapper

# Wrap a method inside a transaction
def transaction(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        our_transaction = not self.transaction

        if our_transaction:
            # Start a transaction
            self.transaction = True

        try:
            func_ret = func(self, *args, **kwargs)
        except:
            # try to roll back
            try:
                if our_transaction:
                    self.transaction = False
            except:
                pass

        if our_transaction:
            self._submit_transaction()

###########################################################################
# Loadbalancer
###########################################################################
class Lb(object):
    _version = 11

    def __init__(self, host, username, password, versioncheck=True):

        self._host         = host
        self._username     = username
        self._versioncheck = versioncheck

        self._transport = bigsuds.BIGIP(host, username, password)
        version = self._transport.System.SystemInfo.get_version()
        if versioncheck and not 'BIG-IP_v11' in version:
            raise UnsupportedF5Version('This class only supports BIG-IP v11', version)

        self._active_folder       = self.active_folder
        self._recursive_query     = self.recursive_query
        self._transaction         = self.transaction
        self._transaction_timeout = self.transaction_timeout

    def __repr__(self):
        return "f5.Lb('%s')" % (self._host)

    ###########################################################################
    # Properties
    ###########################################################################
    @property
    def host(self):
        return self._host

    @property
    def username(self):
        return self._username

    @property
    def versioncheck(self):
        return self._versioncheck

    #### active_folder ####
    @property
    def active_folder(self):
        self._active_folder = self._get_active_folder()
        return self._active_folder

    @active_folder.setter
    def active_folder(self, value):
        self._set_active_folder(value)
        self._active_folder =  value

    #### recursive_query ####
    @property
    def recursive_query(self):
        recursive_query_state = self._get_recursive_query_state()
        if recursive_query_state == 'STATE_ENABLED':
            self._recursive_query =  True
        elif recursive_query_state == 'STATE_DISABLED':
            self._recursive_query =  False
        else:
            raise RuntimeError('Unknown status %s received for recursive_query_state') % (recursive_query_state)

        return self._recursive_query

    @recursive_query.setter
    def recursive_query(self, value):
        if value == True:
            recursive_query_state = 'STATE_ENABLED'
        elif value == False:
            recursive_query_state = 'STATE_DISABLED'
        else:
            raise ValueError('recursive_query must be one of True/False, not %s' % (value))

        self._set_recursive_query_state(recursive_query_state)
        self._recursive_query = value

    #### transaction ####
    @property
    def transaction(self):
        self._transaction = self._active_transaction()
        return self._transaction

    @transaction.setter
    def transaction(self,value):
        if value == True:
            self._ensure_transaction()
            self._transaction = True
        elif value == False:
            self._ensure_no_transaction()
            self._transaction = False

    #### transaction_timeout ####
    @property
    def transaction_timeout(self):
        self._transaction_timeout = self._get_transaction_timeout()
        return self._transaction_timeout

    @transaction_timeout.setter
    def transaction_timeout(self, value):
        self._set_transaction_timeout(value)
        self._transaction_timeout = value

    ###########################################################################
    # INTERNAL API
    ###########################################################################

    #### Session methods ####
    def _ensure_transaction(self):
        wsdl = self._transport.System.Session
        try:
            wsdl.start_transaction()
        except ServerError as e:
            if 'Only one transaction can be open at any time' in e.message:
                pass
            else:
                raise

    def _ensure_no_transaction(self):
        wsdl = self._transport.System.Session
        try:
            wsdl.rollback_transaction()
        except ServerError as e:
            if 'No transaction is open to roll back.' in e.message:
                pass
            else:
                raise
        except:
            raise

    def _submit_transaction(self):
        wsdl = self._transport.System.Session
        wsdl.submit_transaction()

    def _rollback_transaction(self):
        wsdl = self._transport.System.Session
        wsdl.rollback_transaction()

    def _get_transaction_timeout(self):
        wsdl = self._transport.System.Session
        return wsdl.get_transaction_timeout()

    def _set_transaction_timeout(self, value):
        wsdl = self._transport.System.Session
        wsdl.set_transaction_timeout(value)

    # Currently the only way of finding out if there's an active transaction
    # is to actually try starting another one :/
    def _active_transaction(self):
        wsdl = self._transport.System.Session
        try:
            wsdl.start_transaction()
        except ServerError as e:
            if 'Only one transaction can be open at any time' in e.message:
                return True
            else:
                raise

        wsdl.rollback_transaction()
        return False

    def _get_active_folder(self):
        wsdl = self._transport.System.Session
        return wsdl.get_active_folder()

    def _set_active_folder(self, folder):
        wsdl = self._transport.System.Session
        return wsdl.set_active_folder(folder)

    def _get_recursive_query_state(self):
        wsdl = self._transport.System.Session
        return wsdl.get_recursive_query_state()

    def _set_recursive_query_state(self, state):
        wsdl = self._transport.System.Session
        wsdl.set_recursive_query_state(state)

    #### Node methods ####
    def _nodes_get(self):
        wsdl = self._transport.LocalLB.NodeAddressV2
        return wsdl.get_list()

    def _nodes_get_address(self, names):
        wsdl = self._transport.LocalLB.NodeAddressV2
        return wsdl.get_address(names)

    def _nodes_get_connection_limit(self, names):
        wsdl = self._transport.LocalLB.NodeAddressV2
        return wsdl.get_connection_limit(names)

    def _nodes_get_description(self, names):
        wsdl = self._transport.LocalLB.NodeAddressV2
        return wsdl.get_description(names)

    def _nodes_get_dynamic_ratio(self, names):
        wsdl = self._transport.LocalLB.NodeAddressV2
        return wsdl.get_dynamic_ratio(names)

    def _nodes_get_rate_limit(self, names):
        wsdl = self._transport.LocalLB.NodeAddressV2
        return wsdl.get_rate_limit(names)

    def _nodes_get_ratio(self, names):
        wsdl = self._transport.LocalLB.NodeAddressV2
        return wsdl.get_ratio(names)

    #### Pool methods ####
    def _pools_get_description(self, names):
        wsdl = self._transport.LocalLB.Pool
        return wsdl.get_description(names)

    def _pools_get_lbmethod(self, names):
        wsdl = self._transport.LocalLB.Pool
        return wsdl.get_lb_method(names)

    def _pools_get_members(self, names):
        wsdl = self._transport.LocalLB.Pool
        return wsdl.get_member_v2(names)

    def _pools_get_list(self):
        wsdl = self._transport.LocalLB.Pool
        return wsdl.get_list()

    def _pools_get_member(self, pools):
        wsdl = self._transport.LocalLB.Pool
        return wsdl.get_member_v2(pools)

    def _pools_get_member_address(self, pools, ipaddrsq2):
        wsdl = self._transport.LocalLB.Pool
        return wsdl.get_member_address(pools, ipaddrsq2)

    def _pools_get_member_connection_limit(self, pools, ipaddrsq2):
        wsdl = self._transport.LocalLB.Pool
        return wsdl.get_member_connection_limit(pools, ipaddrsq2)

    def _pools_get_member_description(self, pools, ipaddrsq2):
        wsdl = self._transport.LocalLB.Pool
        return wsdl.get_member_description(pools, ipaddrsq2)

    def _pools_get_member_dynamic_ratio(self, pools, ipaddrsq2):
        wsdl = self._transport.LocalLB.Pool
        return wsdl.get_member_dynamic_ratio(pools, ipaddrsq2)

    def _pools_get_member_priority(self, pools, ipaddrsq2):
        wsdl = self._transport.LocalLB.Pool
        return wsdl.get_member_priority(pools, ipaddrsq2)

    def _pools_get_member_rate_limit(self, pools, ipaddrsq2):
        wsdl = self._transport.LocalLB.Pool
        return wsdl.get_member_rate_limit(pools, ipaddrsq2)

    def _pools_get_member_ratio(self, pools, ipaddrsq2):
        wsdl = self._transport.LocalLB.Pool
        return wsdl.get_member_ratio(pools, ipaddrsq2)

    def _pools_get_member_objects(self, pools, addrportsq2, minimal=False):
        pms = []

        # F5 skips empty lists in the sequence causing a mismatch in list indices,
        # so we have to remove empty pools before  we can fetch other attributes.
        f5.util.prune_f5_lists(addrportsq2, pools)

        # Return an empty list if we pruned all pools (i.e. all pools were empty)
        if not pools:
            return []

        if not minimal:
            address2          = self._pools_get_member_address(pools, addrportsq2)
            connection_limit2 = self._pools_get_member_connection_limit(pools, addrportsq2)
            description2      = self._pools_get_member_description(pools, addrportsq2)
            dynamic_ratio2    = self._pools_get_member_dynamic_ratio(pools, addrportsq2)
            priority2         = self._pools_get_member_priority(pools, addrportsq2)
            rate_limit2       = self._pools_get_member_rate_limit(pools, addrportsq2)
            ratio2            = self._pools_get_member_ratio(pools, addrportsq2)

        for idx, addrportsq in enumerate(addrportsq2):
            for idx_inner, addrport in enumerate(addrportsq):
                pm    = f5.Poolmember(addrport['address'], addrport['port'], pools[idx])
                pm.lb = self

                if not minimal:
                    pm._address          = address2[idx][idx_inner]
                    pm._connection_limit = connection_limit2[idx][idx_inner]
                    pm._description      = description2[idx][idx_inner]
                    pm._dynamic_ratio    = dynamic_ratio2[idx][idx_inner]
                    pm._priority         = priority2[idx][idx_inner]
                    pm._rate_limit       = rate_limit2[idx][idx_inner]
                    pm._ratio            = ratio2[idx][idx_inner]

                pms.append(pm)

        return pms

    def _pools_get_objects(self, names, minimal=False):
        """Returns a list of pool objects from a list of pool names"""
        pools = []

        if not minimal:
            descriptions = self._pools_get_description(names)
            lbmethods    = self._pools_get_lbmethod(names)
            members      = self._pools_get_members(names)

        for idx,name in enumerate(names):
            pool              = f5.Pool(name, lb=self)

            if not minimal:
                pool._description = descriptions[idx]
                pool._lbmethod    = lbmethods[idx]
                pool._members     = [
                    f5.Poolmember(ap['address'], ap['port'], pool, lb=self) for ap in members[idx]
                ]

            pools.append(pool)

        return pools

    #### Node methods ####
    def _nodes_get_objects(self, names, minimal=False):
        """Returns a list of node objects from a list of node names"""
        nodes = []

        if not names:
            return nodes

        if not minimal:
            addresses         = self._nodes_get_address(names)
            connection_limits = self._nodes_get_connection_limit(names)
            descriptions      = self._nodes_get_description(names)
            dynamic_ratios    = self._nodes_get_dynamic_ratio(names)
            rate_limits       = self._nodes_get_rate_limit(names)
            ratios            = self._nodes_get_ratio(names)

        for idx,name in enumerate(names):
            node = f5.Node(name, lb=self)

            if not minimal:
                node._address          = addresses[idx]
                node._connection_limit = connection_limits[idx]
                node._description      = descriptions[idx]
                node._dynamic_ratio    = dynamic_ratios[idx]
                node._rate_limit       = rate_limits[idx]
                node._ratio            = ratios[idx]

            nodes.append(node)

        return nodes
    ###########################################################################
    # PUBLIC API
    ###########################################################################
    def submit_transaction(self):
        self._submit_transaction()
    
    @recursivereader
    def pools_get(self, pattern=None, minimal=False):
        pools = self._pools_get_list()

        if pattern is not None:
            if not isinstance(pattern, re._pattern_type):
                pattern = re.compile(pattern)
            pools = filter(lambda pool: pattern.match(pool), pools)

        return self._pools_get_objects(pools, minimal)

    def pool_get(self, name):
        """Returns a single F5 pool"""
        pool = f5.Pool(name, lb=self)
        pool.refresh()

        return pool

    def pm_get(self, node, port, pool):
        """Returns a single F5 poolmember"""

        pm = f5.Poolmember(node, port, pool, lb=self)
        pm.refresh()

        return pm

    @recursivereader
    def pms_get(self, pools=None, pattern=None, minimal=False):
        """Returns a list of F5 poolmembers, takes optional list of pools and pattern"""

        if pools is not None:
            if isinstance(pools, list):
                pass
            else:
                pools = [pools]
        else:
            pools = self._pools_get_list()

        addrportsq2 = self._pools_get_member(pools)

        if pattern is not None:
            if not isinstance(pattern, re._pattern_type):
                pattern = re.compile(pattern)
            for idx,addrportsq in enumerate(addrportsq2):
                addrportsq2[idx] = filter(
                        lambda ap: pattern.match('%s:%s' % (ap['address'], ap['port'])), addrportsq)

        return self._pools_get_member_objects(pools, addrportsq2, minimal)

    def pm_move(self, pm, pool):
        """Moves an existing pm to another pool and returns a reference"""

        pm_copy = copy(pm)
        pm_copy._pool = pool
        pm_copy.save()

        # Delete the copy if we fail to delete ourself so we don't end up
        # with 2 pm's
        try:
            pm.delete()
        except:
            pm_copy.delete()
            raise

        return pm_copy

    def pm_copy(self, pm, pool):
        """Copies an existing pm to another pool and returns a reference"""

        pm_copy = copy(pm)
        pm_copy._pool = pool
        pm_copy.save()

        return pm_copy

    def node_get(self, name):
        node = f5.Node(name=name, lb=self)
        node.refresh()

        return node

    @recursivereader
    def nodes_get(self, pattern=None, minimal=False):
        nodes = self._nodes_get()
        if pattern is not None:
            if not isinstance(pattern, re._pattern_type):
                pattern = re.compile(pattern)
            nodes = filter(lambda node: pattern.match(node), nodes)

        return self._nodes_get_objects(nodes, minimal)

    def rule_get(self, name):
        rule = f5.Rule(name=name, lb=self)
        rule.refresh()

        return rule
