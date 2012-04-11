import boto, time
from fabric.api import env
from fabric.colors import *

class Provider(object):
    def create_instance(self):
        raise NotImplementedError('create_instance')

class ec2(Provider):
    def create_instance(self):
        """Creates an EC2 Instance"""

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