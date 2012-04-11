# Flabric

### Getting Started
Install Flabric:

    $ pip install https://github.com/mattupstate/flabric/tarball/develop

Configure an rcfile with the following values (for EC2):

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

Add the following to your fabfile:

    import flabric

    def create_server():
        flabric.create_server()

    def setup_server():
        flabric.setup_server()

Create the server:

    $ fab -c rcfile create_server

If something doesn't go right during server setup, such as a network error you can try it again by running:

    $ fab -c rcfile setup_server

After the server is finished being created you'll want to uncomment and modify the `host_string` value in your rcfile to perform any more operations on your new server.