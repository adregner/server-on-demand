# This will normally be included in the composite file that
# the bootstrap process uploads to a new server
try:
    my_id = instance_id()
except NameError:
    from serverondemand.xen import instance_id, instance_region
    my_id = instance_id()

import os
import requests

username = RS_USERNAME
apikey = RS_APIKEY

payload = '{"auth": {"RAX-KSKEY:apiKeyCredentials": {"username": "%s", "apiKey": "%s"}}}' % (username, apikey)
headers = {'content-type': 'application/json'}
r = requests.post('https://identity.api.rackspacecloud.com/v2.0/tokens', data = payload, headers = headers)
token = r.json()['access']['token']['id']
tenant = r.json()['access']['token']['tenant']['name']

server_url = 'https://%s.servers.api.rackspacecloud.com/v2/%s/servers/%s' % (instance_region(), tenant, my_id)
headers = {'x-auth-token': token}
requests.delete(server_url, headers = headers)
