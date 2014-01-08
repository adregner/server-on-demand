server-on-demand
================

Spins up a Rackspace Cloud Server to run a single task, and provides an easy way to kill it off when its done.

Whats the point?
----------
Cloud servers are meant to be disposable, and they are very useful and economical to spin up for a medium to large sized task and then destroy when it's done.  This allows you to only pay for the minutes / hours that the server was up and not have to have something running long-term that you aren't using all the time.

This will spin up such a server and prepare it for your job, and run your job.  It won't wait for the job to complete so you can easily use `demand_server` in a script or crontab and check in on the results of your task later.  It allows you to specify any and all parameters of the server it will create (image, flavor, other Rackspace Next-Gen Cloud Servers parameters, etc...)

The icing on the cake is that this script will create a script on the new server from a template that will allow you or your code running on this ephemeral cloud server to easily delete it self.  Just call `demand_done` from inside your new server and it will make a call to the Rackspace Cloud Servers API to delete itself.  (This will of course destroy any and all data you have on the server, and nothing is done to save or image any of it, so make sure you've already examined or stored it elsewhere.)

Usage
--------
```
demand_server [-h] [--debug] [--credentials CREDENTIALS]
                     [--region REGION] [--image IMAGE] [--flavor FLAVOR]
                     [--script SCRIPT] [--yes]
                     ...

Spin up a server to do a thing, and then have it die.

positional arguments:
  command

optional arguments:
  -h, --help            show this help message and exit
  --debug, -d
  --credentials CREDENTIALS, -c CREDENTIALS
                        Credentials file with API username and key.
                        [~/.rackspace_cloud_credentials]
  --region REGION, -r REGION
                        Region to use [Identity default]
  --image IMAGE, -i IMAGE
                        Image name or substring of a name to boot. [Ubuntu]
  --flavor FLAVOR, -f FLAVOR
                        Flavor to boot. [512 MB / ID=2]
  --script SCRIPT, -s SCRIPT
                        Script to be uploaded and ran on the server.
  --yes, -y             Auto-confirm any action the script makes.
```
