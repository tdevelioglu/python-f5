from bigsuds import ServerError
import f5.lb
import weakref

# Abstract Factory class for generating cached F5 objects
class CachedFactory(object):
    def __init__(self, Klass):
        self._Klass = Klass
        self._cache = weakref.WeakValueDictionary()

    def __repr__(self):
        return 'CachedFactory(%s)' % self._Klass

    def get(self, name, lb=None, *args, **kwargs):
        key = name
        if lb is not None:
            key = lb.host + key

        # Save some bytes
        key = hash(key)

        if key in self._cache:
            return self._cache[key]
        else:
            obj = self._Klass(name, *args, lb=lb, **kwargs)

            self._cache[key] = obj
            return obj

    def put(self, obj):
        key = obj.name
        if obj.lb is not None:
            key = obj.lb.host + key

        key = hash(key)
        self._cache[key] = obj

# Looks at the first list for empty lists and removes elements in the same position from all lists
# including itself.
def prune_f5_lists(list1, *lists):
    for list in lists:
        if len(list) != len(list1):
            raise ValueError('Lists must be of equal length')

    idx_remove = []
    for idx, val in enumerate(list1):
        if val == []:
            for list in lists:
                list[idx] = None

    for list in lists:
        while None in list:
            list.remove(None)

    while [] in list1:
        list1.remove([])

###########################################################################
# Decorators
###########################################################################
from functools import wraps

# Ensure class instance cache is updated on a key attribute change
def updatefactorycache(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        func_ret = func(self, *args, **kwargs)
        self.factory.put(self)
        return func_ret

    return wrapper


# Wrap a method inside a transaction (non-lb version)
def lbtransaction(func):
    @wraps(func)
    @lbwriter
    def wrapper(self, *args, **kwargs):
        # Only if there is no existing transaction
        our_transaction = not self._lb.transaction

        if our_transaction:
            # Start a transaction
            self._lb.transaction = True

        try:
            func_ret = func(self, *args, **kwargs)
        except:
            # try to roll back
            try:
                if our_transaction:
                    self._lb.transaction = False
            except:
                pass

            raise

        if our_transaction:
            self._lb._submit_transaction()

    return wrapper


#### Throw an exception if there's no valid lb set ####
def lbmethod(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not isinstance(self._lb, f5.Lb):
            raise RuntimeError('lb must be a valid lb object, not %s' % (type(self.lb).__name__))

        return func(self, *args, **kwargs)

    return wrapper


# Set active folder to writable one if it is not
def lbwriter(func):
    @wraps(func)
    @lbmethod
    @lbrestore_session_values
    def wrapper(self, *args, **kwargs):
        if self._lb._active_folder == '/':
            self._lb.active_folder = '/Common'

        return func(self, *args, **kwargs)

    return wrapper


# Restore session attributes to their original values if they were changed
def lbrestore_session_values(func):
    def wrapper(self, *args, **kwargs):
        original_folder          = self._lb._active_folder
        original_recursive_query = self._lb._recursive_query

        func_ret = func(self, *args, **kwargs)

        if self._lb._active_folder != original_folder:
            self._lb.active_folder = original_folder

        if self._lb._recursive_query != original_recursive_query:
            self._lb.recursive_query = original_recursive_query

        return func_ret

    return wrapper
