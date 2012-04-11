# Flabric

Flabric allows you to easily create and configure servers for Python projects on Amazon EC2 or Rackspace Cloud Servers.

## Getting Started

### Installation

Install Flabric:

    $ pip install https://github.com/mattupstate/flabric/tarball/develop

#### EC2:

Install boto:

    $ pip install boto

Configure an rcfile with the following values:

    user = ubuntu
    key_filename = /path/to/keyfile
    #host_string = to be added later

    server_provider = ec2
    server_type = flabric.ubuntu.nginx_uwsgi_supervisor

    ec2_key = your_ec2_key
    ec2_secret = your_ec2_secret
    ec2_ami = ami-fd589594
    ec2_keypair = keypair_name
    ec2_secgroups = security_group_name
    ec2_instancetype = t1.micro

#### Rackspace:

Install python-cloudservers:

    $ pip install python-cloudservers

Configure an rcfile with the following values:

    user = root
    password = your_custom_password
    #host_string = to be added later

    server_provider = rackspace
    server_type = flabric.ubuntu.nginx_uwsgi_supervisor

    rackspace_username = your_username
    rackspace_apikey = your_api_key
    rackspace_servername = your_server_name
    rackspace_image = 112
    rackspace_flavor = 1

### Create a Server

Add the following to your fabfile:

    import flabric

    def create_server():
        flabric.create_server()

    def setup_server():
        flabric.setup_server()

Create the server:

    $ fab -c rcfile create_server

If you've already created your server through your respective management console, or if something fails during server setup, you can run setup by setting the value for `host_string` in your rcfile running to your server's public DNS or IP address and running:

    $ fab -c rcfile setup_server

After the server is finished being created you'll want to uncomment and modify the `host_string` value in your rcfile to perform any more operations on your new server.