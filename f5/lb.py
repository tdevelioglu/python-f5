import bigsuds
import f5
import f5.util
import re

from bigsuds import ServerError
from copy import copy
from functools import reduce

from .exceptions import (
    UnsupportedF5Version, NodeNotFound, PoolNotFound, PoolMemberNotFound,
    RuleNotFound, VirtualServerNotFound
)


# 'http://pingfive.typepad.com/blog/2010/04/deep-getattr-python-function.html'
def deepgetattr(obj, attr):
    """Recurses through an attribute chain to get the ultimate value."""
    return reduce(getattr, attr.split('.'), obj)

###########################################################################
# Decorators
###########################################################################
from functools import wraps

# Restore session attributes to their original values if they were changed
def restore_session_values(func):
    @wraps(func)
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


###########################################################################
# Loadbalancer
###########################################################################
class Lb(object):
    _version = 11

    def __init__(self, host, username, password, versioncheck=True,
                use_session=True, verify=True):

        self._host         = host
        self._username     = username
        self._versioncheck = versioncheck
        self._use_session  = use_session
        self._verify       = verify

        if use_session:
            self._transport = bigsuds.BIGIP(
                host, username, password, verify
            ).with_session_id()
        else:
            self._transport = bigsuds.BIGIP(
                host, username, password, verify
            )
        version = self._transport.System.SystemInfo.get_version()
        if versioncheck and not 'BIG-IP_v11' in version:
            raise UnsupportedF5Version('This class only supports BIG-IP v11', version)

        self._active_folder       = self.active_folder
        self._recursive_query     = self.recursive_query
        self._transaction         = self.transaction
        self._transaction_timeout = self.transaction_timeout


    def __repr__(self):
        return "f5.Lb('%s')" % (self._host)

    # call a service on the soap api
    def _call(self, call, *args, **kwargs):
        return deepgetattr(self._transport, call)(*args, **kwargs)

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

    @property
    def use_session(self):
        return self._use_session

    @property
    def verify(self):
        return self._verify

    #### active_folder ####
    @property
    def active_folder(self):
        self._active_folder = self._get_active_folder()
        return self._active_folder

    @active_folder.setter
    def active_folder(self, value):
        self._set_active_folder(value)
        self._active_folder =  value

    #### version
    @property
    def version(self):
        return self._call('System.SystemInfo.get_version')

    #### system_information
    @property
    def system_information(self):
        return self._call('System.SystemInfo.get_system_information')

    #### product_information
    @property
    def product_information(self):
        return self._call('System.SystemInfo.get_product_information')

    #### failover_state
    @property
    def failover_state(self):
        # Truncate value to just the state
        self._failover_state = self._call('System.Failover.get_failover_state')[15:]
        return self._failover_state

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
            if 'Only one transaction can be open at any time' in str(e):
                pass
            else:
                raise

    def _ensure_no_transaction(self):
        wsdl = self._transport.System.Session
        try:
            wsdl.rollback_transaction()
        except ServerError as e:
            if 'No transaction is open to roll back.' in str(e):
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
            if 'Only one transaction can be open at any time' in str(e):
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

    ###########################################################################
    # PUBLIC API
    ###########################################################################
    def submit_transaction(self):
        self._submit_transaction()
    
    def pool_get(self, name):
        """Returns a single F5 pool"""
        try:
            pool = f5.Pool.factory.create([name], self)[0]
            pool.refresh()
        except ServerError as e:
            if 'was not found.' in str(e):
                raise PoolNotFound(name)
            else:
                raise

        return pool

    @recursivereader
    def pools_get(self, pattern=None, minimal=False):
        """Returns a list of F5 Pools, takes optional pattern"""
        return f5.Pool._get(self, pattern, minimal)

    def pm_get(self, node, port, pool):
        """Returns a single F5 PoolMember"""
        try:
            pm = f5.PoolMember.factory.create((node, port, pool), self)[0]
            pm.refresh()
        except ServerError as e:
            if 'was not found.' in str(e):
                raise PoolMemberNotFound((node, port, pool))
            else:
                raise

        return pm

    @recursivereader
    def pms_get(self, pools=None, pattern=None, minimal=False):
        """Returns a list of F5 PoolMembers, takes optional list of pools and pattern"""
        return f5.PoolMember._get(self, pools, pattern, minimal)

    def node_get(self, name):
        """Returns a single F5 Node"""
        try:
            node = f5.Node.factory.create([name], self)[0]
            node.refresh()
        except ServerError as e:
            if 'was not found.' in str(e):
                raise NodeNotFound(name)
            else:
                raise

        return node

    @recursivereader
    def nodes_get(self, pattern=None, minimal=False, partition='/'):
        """Returns a list of F5 Nodes, takes optional list of pools and pattern"""
        return f5.NodeList(self, pattern, partition, minimal)

    def rule_get(self, name):
        """Returns a single F5 Rule"""
        try:
            rule = f5.Rule.factory.create([name], self)[0]
            rule.refresh()
        except ServerError as e:
            if 'was not found.' in str(e):
                raise RuleNotFound(name)
            else:
                raise

        return rule

    @recursivereader
    def rules_get(self, pattern=None, minimal=False):
        """Returns a list of F5 Rules, takes optional pattern"""
        return f5.Rule._get(self, pattern, minimal)

    def vs_get(self, name):
        """Returns a single F5 VirtualServer"""
        try:
            vs = f5.VirtualServer.factory.create([name], self)[0]
            vs.refresh()
        except ServerError as e:
            if 'was not found.' in str(e):
                raise VirtualServerNotFound(name)
            else:
                raise

        return vs

    @recursivereader
    def vss_get(self, pattern=None, minimal=False):
        """Returns a list of F5 VirtualServers, takes optional pattern"""
        return f5.VirtualServer._get(self, pattern, minimal)

    @recursivereader
    def pools_get_vs(self, pools=None, minimal=False):
        """Returns VirtualServers associated with a list of Pools"""
        if pools is None:
            pools = f5.Pool._get_list(self)
        else:
            if isinstance(pools[0], f5.Pool):
                pools = [pool.name for pool in pools]

        result = {pool: [] for pool in pools}

        vss = f5.VirtualServer._get(self, minimal=minimal)
        if minimal is True:
            vss = f5.VirtualServer._refresh_default_pool(self, vss)

        for pool in pools:
            for vs in vss:
                print(vs._default_pool)
                if pool == vs._default_pool.name:
                    result[pool].append(vs)

        return result
