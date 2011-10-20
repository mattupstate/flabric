# Flask-Fabric
Flask-Fabric is a so-called skeleton/template project for a [Flask](http://flask.pocoo.org) application and ships with a [Fabric](http://www.fabfile.org) deployment system for Amazon EC2. It is directly inspired by [Fabulous](https://github.com/gcollazo/Fabulous) but has some significant differences as well.

The goal of Flask-Fabric is to make setting up a Flask app and deploying it to EC2 a trivial task. Something being 'trivial' is very subject, but this project can immediately be deployed by cloning the project, configuring an rcfile, and running a fabric task.

### Getting Started
Clone the project and install the requirments using pip (hopefully you use pip)

    $ git clone git@github.com:mattupstate/flask-fabric.git
    $ cd flask-fabric
    $ pip install -r requirements.txt

Copy `rcfile.sample` and name it `rcfile.development` (or staging, or production). Then edit the following values in `rcfile.development`:

    ec2_key # Your EC2 account key
    ec2_secret # Your EC2 account secret
    ec2_keypair # A keypair name you've created under your account
    ec2_secgroups # A comma separated list of security groups

Save the file and then run:

    $ fab -c rcfile.development create_server

If you're rcfile is configured correctly you can now sit back and relax while Fabric creates an Ubuntu EC2 instance and installs:

* [nginx](http://wiki.nginx.org/)
* [uWSGI](http://projects.unbit.it/uwsgi/)
* [memcached](http://memcached.org/)
* [pip](http://www.pip-installer.org/)
* [virtualenv](http://www.virtualenv.org/)
* [virtualenvwrapper](http://www.doughellmann.com/projects/virtualenvwrapper/)
* [uwsgi-manager](https://github.com/mattupstate/uWSGI-Manager)
* [git](http://git-scm.com/)
    
It will then deploy the application to the server immediately. Once this is complete, you'll want to edit `rcfile.development` again and set the following values:

    key_filename # Path to keypair.pem
    host_string # The host name of the instance that was launched

Now you're ready to deploy a new version after you commit some code to the git repository. To redeploy run:

    $ fab -c rcfile.development deploy

Explore the fabfile for more tasks that allow you to manage nginx and the uwsgi process manager