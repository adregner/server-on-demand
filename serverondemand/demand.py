import os
import time
import logging
import pyrax
from pyrax.utils import wait_for_build
from paramiko import RSAKey

from serverondemand import get_resource
from serverondemand.xen import instance_id, instance_name
from serverondemand.executor import Executor

logger = logging.getLogger(__name__)

def servers_api(creds_file, region = None):
    """Sets up a pyrax instance for Cloud Servers in the given region."""
    pyrax.set_setting("identity_type", "rackspace")
    pyrax.set_credential_file(os.path.expanduser(creds_file), region = region)
    cs = pyrax.cloudservers

    return cs

class Demand(object):
    def __init__(self, args):
        self.debug = not not args.debug
        self.script = args.script if os.path.isfile(args.script) else False
        self.server = None

        region = args.region.upper() if args.region else None
        self.api = servers_api(args.credentials, region)

        if args.agent_creds:
            self.agent_username = args.agent_creds['username']
            self.agent_apikey = args.agent_creds['apikey']
        else:
            logger.debug("Loading agent credentials from %s" % args.credentials)
            from ConfigParser import SafeConfigParser
            parser = SafeConfigParser()
            parser.read(os.path.expanduser(args.credentials))
            self.agent_username = parser.get('rackspace_cloud', 'username')
            self.agent_apikey = parser.get('rackspace_cloud', 'api_key')

    def build(self, image, flavor, **kwargs):
        """Builds a server and runs the requested script on it.

        image and flavor are values that will be recognized by the novaclient library
        as references to an image and a flavor to use to boot the server with.

        Optionally, other kewword arguments can be passed and will be passed allong to
        the novaclient.boot method to enable other things such as more metadata, disk
        configuration options, network interfaces, etc...
        """
        logger.debug("Generating new SSH key")
        name = "serverondemand-%s" % str(time.time()).replace('.', '-')

        key = RSAKey.generate(2048)
        personality = {
                "/root/.ssh/authorized_keys": "ssh-rsa %s serverondemand generated key\n" % key.get_base64(),
                }
        meta = {
                'origin': 'serverondemand',
                }

        if kwargs.get('meta', None):
            meta.update(kwargs.pop('meta'))
        if kwargs.get('files', None):
            personality.update(kwargs.pop('files'))

        logger.info("Building server")

        server = self.api.servers.create(name, image, flavor, meta = meta, files = personality, **kwargs)
        server = wait_for_build(server, verbose = self.debug)

        self.server = server
        self.key = key

        logger.info("Uploading bootstrap")
        self.bootstrap()
        logger.info("Executing scripts")
        self.run_script()

        # all done

    def bootstrap(self):
        """Uploads scripts to the server.

        Creates the demand_done script which the new server can use to delete
        itself, along with the bootstrap.sh script that sets up useful things."""
        executor = Executor(self.server.accessIPv4, 'root', self.key)
        sftp = executor.open_sftp()

        self._write_sftp_file(sftp, '/usr/sbin/demand_done', mode=0755, data =
                "#!/usr/bin/env python\n" +
                "RS_USERNAME='%s'\n" % self.agent_username +
                "RS_APIKEY='%s'\n" % self.agent_apikey +
                get_resource('xen.py') +
                get_resource('resources/demand_done.py'))

        self._write_sftp_file(sftp, '/root/bootstrap.sh',
                get_resource('resources/bootstrap.sh'), 0755)

        if self.script:
            with open(self.script, 'r') as fd:
                self._write_sftp_file(sftp, '/root/script.sh', fd.read(), 0755)

        executor.close()

    def _write_sftp_file(self, sftp, path, data, mode = 0644):
        fd = sftp.open(path, 'w')
        fd.chmod(mode)
        written = fd.write(data)
        fd.close()
        return written

    def run_script(self):
        """Runs the scripts on the server.

        First runs the bootstrap.sh script we generated, and waits for it to complete.

        If the user provided a script of their own, it runs that too, but detatches
        and lets it run in the background."""
        executor = Executor(self.server.accessIPv4, 'root', self.key, debug = self.debug)

        res = executor.run("/root/bootstrap.sh")
        logger.debug("Bootstrap script: %s" % res)

        logger.info("Running user script.sh detatched.")
        if self.script:
            res = executor.run("nohup /root/script.sh")

        executor.close()

    def get_flavor(self, ref):
        """Finds the perfect server flavor

        Pass in a flavor ID and it will return the Flavor object with its name et. al.

        # TODO I'd love a nice way to lazy specify what type of flavor we want """
        #if 'GB' not in ref and 'MB' not in ref:
        flavor = self.api.flavors.get(ref)
        return flavor.name, flavor.id

        #potential = [ flv for flv in self.api.flavors.list()
        #        if substr in flv.name.replace(' ', '') ]
        #logger.debug("Potential Flavors: %s" % [flv.name for flv in potential])

        #potential.sort(cmp = lambda a, b: 1 if a.name > b.name else -1)
        #flavor = potential[-1]

        #return flavor.name, flavor.id

    def get_image(self, substr):
        """Finds the perfect server image

        Pass in a random string and it will find the "highest" image that
        contains that string in its name.  Useful for getting the most recent
        "Ubuntu" image or something like that."""
        potential = [ img for img in self.api.images.list()
                if substr.lower() in img.name.lower() ]
        logger.debug("Potential Images: %s" % [img.name for img in potential])

        potential.sort(cmp = lambda a, b: 1 if a.name > b.name else -1)
        image = potential[-1]

        return image.name, image.id

