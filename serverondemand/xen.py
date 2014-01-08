import os
import re

XENBUS = ["/var/run/xenstored/socket", "/proc/xen/xenbus"]

def get_xenbus():
    for f in XENBUS:
        if os.path.isfile(f):
            return f

    raise RuntimeError("Cannot find xenbus")

def xenbus_read(key):
    env_key = ("XENBUS_%s" % re.sub('[-/]', '_', key)).upper()

    # allow a local override for testing and odd situations
    if env_key in os.environ:
        return os.environ[env_key]

    # this is easier and faster then forking a subprocess, i promise
    fd = os.open(get_xenbus(), os.O_RDWR)
    length = chr(len(key) + 1)
    os.write(fd, "\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"+length+"\x00\x00\x00")
    os.write(fd, key+"\x00")

    junk = os.read(fd, 16)
    data = os.read(fd, 512)
    os.close(fd)

    return data

def instance_id():
    data = xenbus_read("name")
    m = re.search('instance-([a-z0-9-]+)$', data)

    if not m:
        raise RuntimeError("Cannot parse response from xenbus")
    else:
        return m.group(1)

def instance_name():
    return xenbus_read("vm-data/hostname")

def instance_region():
    return xenbus_read("vm-data/provider_data/region")

