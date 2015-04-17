import os
import f5
from getpass import getpass

del os.environ['http_proxy']
del os.environ['https_proxy']

lb = f5.Lb('staticlb-102.ams4.prod.booking.com', 'tdevelioglu',
        getpass())

print(lb.pm_get(f5.Node('/Common/bc101app-04'), 80, f5.Pool('/WWW/www.booking.com_all')))
