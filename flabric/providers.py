import time
from fabric.api import env
from fabric.colors import *

class Provider(object):
    def create_instance(self):
        raise NotImplementedError('create_instance')

class ec2(Provider):
    def create_instance(self):
        """Creates an EC2 Instance"""
        import boto

        print(yellow("Creating EC2 instance"))

        conn = boto.connect_ec2(env.ec2_key, env.ec2_secret)
        reservation = conn.run_instances(env.ec2_ami, 
                                         key_name=env.ec2_keypair, 
                                         instance_type=env.ec2_instancetype,
                                         security_groups=env.ec2_secgroups.split(','))
        
        instance = reservation.instances[0]
        time.sleep(3)

        try:
            conn.create_tags([instance.id], {"Name": env.ec2_tag})
        except AttributeError:
            pass
        
        while instance.state == u'pending':
            print(yellow("Instance state: %s" % instance.state))
            time.sleep(10)
            instance.update()

        print(green("Instance state: %s" % instance.state))
        print(green("Public dns: %s" % instance.public_dns_name))
        
        return instance.public_dns_name

class rackspace(Provider):
    def create_instance(self):
        from cloudservers import CloudServers
        from cloudservers.exceptions import NotFound

        cs = CloudServers(env.rackspace_username, env.rackspace_apikey)
        image = cs.images.find(id=int(env.rackspace_image))
        flavor = cs.flavors.find(id=int(env.rackspace_flavor))
        server = cs.servers.create(env.rackspace_servername, image=image, flavor=flavor)
        server_id = server.id

        while True:
            while True:
                try:
                    server = cs.servers.find(id=server_id)
                    break;
                except NotFound:
                    print(yellow('Server not found yet'))
                    time.sleep(10)
                    pass

            if server.status != 'ACTIVE':
                print(yellow("Server status: %s" % server.status))
                time.sleep(20)
                continue
            break

        server.update(password=env.password)
        public_ip = server.addresses['public'][0]

        print server.addresses
        print(green("Instance state: %s" % server.status))
        print(green("Public IP: %s" % public_ip))

        return public_ip