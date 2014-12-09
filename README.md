# Python F5

A library to make manipulating F5 loadbalancers easy

## Overview

- Supports F5 BIG-IP V11
- Manage nodes, pools and poolmembers, irules and virtualservers

## Requires

- python 2.7+ / Python 3+
- bigsuds (https://devcentral.f5.com/d/bigsuds-python-icontrol-library)

## Usage

```bash
python setup.py install
```

### Examples

#### Loadbalancers

```python
import f5
lb = f5.Lb('f5.example.com', 'admin', 'admin')

# Get the failover state
lb.failover_state

# Disable versioncheck if you know better
lb = f5.Lb('f5.example.com', 'admin', 'admin', versioncheck=False)

# Get all intranet pools
pools = lb.pools_get(pattern='.*intranet.*')

# I only need the names - go faster!
# (This will skip populating all the object attributes, useful if you just want a listing)
pools = lb.pools_get(pattern='.*intranet.*', minimal=True)

# Get the members in those pools
pms = lb.pms_get(pools=pools)

# I just wanted the ones in dc3
pms =  lb.pms_get(pools=pools, pattern='.*dc3')

# Just give me ALL poolmembers in dc3
pms =  lb.pms_get(pattern='.*dc3.*')

# Give me *ALL* poolmembers
pms =  lb.pms_get()

# Nodes are similar
nodes = lb.nodes_get()

# Pools
pools = lb.pools_get()

# Change the active folder
if lb.active_folder != '/Common':
    lb.active_folder = '/Common'

# Enable recursive querying
lb.recursive_query = True

# Perform transactions
node = lb.node_get('/Common/node-01')
pm   = lb.get_pm('/Common/node-01'):

lb.transaction = True
do_stuff()

if happy():
    # submit
    lb.submit_transaction()
else:
    # or rollback
    lb.transaction = False
```

#### Nodes

```python
import f5
lb = f5.Lb('f5.example.com', 'admin', 'admin')

# Basic create
node = f5.Node(name='/Common/node-01', address='1.1.1.1', connection_limit=0, lb=lb)
node.save()

# We can check if this node exists
if node.exists():
    print 'Oh, it was already there'
else:
    import nuke
    icbm = nuke.Icbm()
    icbm.launch(target='Juliano')

# this works too
node = f5.Node(name='/Common/node-01')

node.lb                = lb
node._name             = name
node._address          = address
node._connection_limit = connection_limit
node._description      = description
node._dynamic_ratio    = dynamic_ratio
node._enabled          = enabled
node._rate_limit       = rate_limit
node._ratio            = ratio
node.save()

# Get the attributes synchronously (directly from the lb)
print 'node connection_limit: %s' % (node.connection_limit)
print 'node description: %s'      % (node.description)
print 'node dynamic_ratio: %s'    % (node.dynamic_ratio)
print 'node status: %s'           % (node.enabled)
print 'node rate_limit: %s'       % (node.rate_limit)
print 'node rate_limit: %s'       % (node.ratio)

# Often local copies are enough and we don't want to call the lb
print 'node connection_limit: %s' % (node._connection_limit)
print 'node description: %s'      % (node._description)
print 'node dynamic_ratio: %s'    % (node._dynamic_ratio)
print 'node status: %s'           % (node._enabled)
print 'node rate_limit: %s'       % (node._rate_limit)
print 'node rate_limit: %s'       % (node._ratio)

# It's under 9000!
node.ratio = 8999

# This node is broken, disable it
node.enabled = False

# We can also do transactions
lb.transaction = True
node.connection_limit = 100
node.ratio            = 10
lb.submit_transaction()

# we can set attributes asynchronously, but remember to save()
node._connection_limit = 100
node._ratio            = 10
# save() is transactional. (But it won't submit if there's already one running)
node.save()

# We can re-fetch all attributes from the lb easily
node.refresh()

# Or work with a list for convenience:
nodelist = f5.NodeList(lb, pattern='.*webapp.dc02.*')

# Update attributes on all the nodes in the list
nodelist.connection_limit = '9001'

# or asynchronous (and transactional):
nodelist._set_nodeattr('_connection_limit', 9001)
nodelist._set_nodeattr('_description', 'It's over 9000!')
nodelist.sync()

# to dictionary
nodelist.dictionary

# Or from local copies (no requests to the lb, so faster)
nodelist._dictionary

# Load from dictionary:
nodelist.dictionary = dictionary
```

#### Pools

```python
import f5
lb = f5.Lb('f5.example.com', 'admin', 'admin')

# Basic create
pool = f5.Pool(name='/Common/pool-01', lbmethod='ratio_member', members=[], lb=lb)
pool.save()

# This time with a member
node = lb.node_get('/Common/node-01')
# TODO: need some more logic here. pool parameter is redundant when new object is meant to become a member
pm   = f5.PoolMember(node=node, port=80, pool=pool)

pool = f5.Pool(name='/Common/pool-01', lbmethod='ratio_member', members=[pm], lb=lb)

# Get existing pool
pool = lb.pool_get('/Common/pool-01)

# Get pool members
poolmembers = pool.members

# You can directly reference member attributes
poolmembers[0].connection_limit
poolmembers[0].ratio = 10

# Set some attributes synchronously
pool.lbmethod    = 'round_robin'
pool.description = 'This is an example pool'

# or asynchronously (remember to save!)
pool._lbmethod    = 'round_robin'
pool._description = 'This is an example pool'
pool.save()

# We can easily copy members between pools
# Here we copy members in dc3 from 'some_other_pool' to our pool.
pms = lb.pms_get(pools=['some_other_pool'], pattern='.*dc3.*')
pool.members = pms
```

### Poolmembers

```python
import f5
lb = f5.Lb('f5.example.com', 'admin', 'admin')

# Basic create
node = lb.node_get('/Common/node-01')
pool = lb.pool_get('/Common/pool-01)

pm = f5.PoolMember(node=node, port=80, pool=pool, lb=lb)

# We don't *have to* use objects, string are also fine.
pm = f5.PoolMember(node='/Common/node-01', port=80, pool='/Common/pool-01', lb=lb)

# Save it to the lb before using setters (or receive an error)
pm.save()

# Set some attributes synchronously
pm.description = 'This is my poolmember, there are many like it, but this one is mine'
pm.ratio       = 10
pm.lb          = lb

# or asynchronously (remember to save!)
pm._ratio = 10
pm._lb    = lb
pm.save()

# We can defer setting the lb until the very end and still use the setters to make changes
# asynchronously. If lb isn't set, the setters will just update the local copies.
pm = f5.PoolMember(node=node, port=80, pool=pool)

pm.connection_limit = 9000
pm.description      = 'Whos poolmember is this?'
pm.ratio            = 10

pm.lb               = lb
pm.save()

# You can also directly reference the linked node object's attributes
pm.node.connection_limit
pm.node.ratio = 10
```
