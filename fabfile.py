from __future__ import with_statement
import boto
import datetime
import fileinput
import os 
import time
from fabric.api import *
from fabric.colors import *
from fabric.contrib.console import confirm
from deploy.cookbook import recipe

# Timestample
env.timestamp = int(time.mktime(datetime.datetime.now().timetuple()))

# Local cwd
env.lcwd = os.path.dirname(__file__)

# Split security groups
env.ec2_secgroups = env.ec2_secgroups.split(",")

# Generate conventional server values
env.server_user_home_dir = "%(server_home_dir)s/%(user)s" % env
env.server_sites_dir = "%(server_user_home_dir)s/sites" % env
env.server_virtualenv_dir = "%(server_user_home_dir)s/.virtualenv" % env

# Generate conventional application values
env.app_virtualenv = "%(server_virtualenv_dir)s/%(app_id)s" % env
env.app_dir = "%(server_sites_dir)s/%(app_id)s" % env
env.app_var_dir = "%(app_dir)s/var" % env
env.app_run_dir = "%(app_var_dir)s/run" % env
env.app_log_dir = "%(app_var_dir)s/log" % env 
env.app_shared_dir = "%(app_dir)s/shared" % env
env.app_releases_dir = "%(app_dir)s/releases" % env
env.app_current_release = "%(app_releases_dir)s/current" % env
env.app_previous_release = "%(app_releases_dir)s/previous" % env
env.app_config_dir = "%(app_dir)s/etc" % env
env.app_cache_dir = "%(app_shared_dir)s/%(app_cache_dir)s" % env
env.app_instance_dir = "%(app_current_release)s/instance" % env

# Split strings into lists
env.app_admin_emails = env.app_admin_emails.split(",")
env.app_cache_memcached_servers = env.app_cache_memcached_servers.split(",")


# tasks
        
def create_server():
    """
    Create an EC2 instance and install necessary packages and software
    """
    start_time = time.time()
    print(green("Started..."))
    env.host_string = create_instance()
    print(green("Waiting 30 seconds for server to boot..."))
    time.sleep(30)
    _oven()
    end_time = time.time()
    print(green("Runtime: %f minutes" % ((end_time - start_time) / 60)))
    print(green(_render("Instance created. Change the value of host_string your rcfile to %(host_string)s")))
    deploy()
    print("All done! Edit the host_string value in your rcfile to match: %s" % env.host_string)


def clean():
    """
    Remove all temporary build files
    """
    print(green("Removing temporary build files"))
    if os.path.isdir(_render('%(build_dir)s')):
        _local('rm -R %(build_dir)s')
        
def test():
    """
    Run the test suite and bail out if it fails
    """
    print(green("Running application tests", True))
    with settings(warn_only=True):
        with cd(_render("%(lcwd)s")):
            result = _local("nosetests --with-xunit")
            if result.failed and not confirm("Tests failed. Continue anyway?"):
                abort(red("Tests failed. Will not continue."))

def build():
    """
    Run the build process
    """
    clean()
    print(green("Starting build process", True))
    env.app_release = _local('cd %(lcwd)s; git rev-parse %(app_scm_branch)s | cut -c 1-9', capture=True)
    env.build_dir = _render("%(build_dir)s/%(app_release)s")
    print(green(_render("Release hash: %s(app_release)s")))
    _local('mkdir -p %(build_dir)s')
    bundle_code()
    generate_configuration()

def bundle_code():
    """
    Create an archive from the target branch for the current host(s)
    """
    print(green(_render("Bundling code"), True))
    print(green(_render("Repository: %(app_scm_url)s")))
    print(green(_render("Branch: %(app_scm_branch)s")))
    env.app_bundle_tar = _render('%(build_dir)s/%(app_release)s.tar')
    _local('git archive --format=tar %(app_scm_branch)s > %(app_bundle_tar)s')
    
def generate_configuration():
    """
    Generate configuration files from the environment
    """
    print(green(_render("Generating configuration"), True))
    _local('mkdir -p %(build_dir)s/etc')
    open(_render('%(build_dir)s/etc/config.py'), 'w').write(_render(open(_render('%(lcwd)s/etc/config.py.tmpl'), 'r').read()))
    open(_render('%(build_dir)s/etc/nginx.conf'), 'w').write(_render(open(_render('%(lcwd)s/etc/nginx.conf.tmpl'), 'r').read()))
    open(_render('%(build_dir)s/etc/uwsgi.yaml'), 'w').write(_render(open(_render('%(lcwd)s/etc/uwsgi.yaml.tmpl'), 'r').read()))

def generate_local_config():
    """
    Generate a local configuration for running the application using the builtin webserver
    """
    print(green(_render("Generating local configuration"), True))
    _local('if [ -e %(lcwd)s/instance/config.py ];then rm %(lcwd)s/instance/config.py; fi;')
    output = _render(open(_render('%(lcwd)s/etc/config.py.tmpl'), 'r').read())
    open(_render('%(lcwd)s/instance/config.py'), 'w').write(output)
    print(green(_render('Successfully generated %(lcwd)s/instance/config.py >>>')))
    print(yellow(open(_render('%(lcwd)s/instance/config.py'), 'r').read()))

def upload_release():
    """
    Upload and extract the release into a release folder
    """
    print(green(_render("Uploading release"), True))
    require('app_release', provided_by=[build])
    require('app_bundle_tar', provided_by=[bundle_code])
    env.app_release_dir = _render('%(app_releases_dir)s/%(app_release)s')
    env.app_release_tar = _render('%(server_user_home_dir)s/%(app_release)s.tar.gz')
    _sudo('if [ -d %(app_release_dir)s ];then rm -r %(app_release_dir)s; fi;')
    _put({"file": "%(app_bundle_tar)s", "destination": "%(app_release_tar)s"})
    _run('mkdir %(app_release_dir)s')
    print(green(_render("Extracting release"), True))
    _run('cd %(app_release_dir)s; tar -xvf %(app_release_tar)s')
    _run('rm %(app_release_tar)s')

def upload_configuration():
    """
    Upload generated configuration files
    """
    print(green(_render("Uploading configuration files"), True))
    etc_files = os.listdir(_render('%(build_dir)s/etc'))
    for file in etc_files:
        _put({"file":'%s/etc/%s' % (env.build_dir, file), "destination":'%s/%s' % (env.app_instance_dir, file)})

def update_virtualenv():
    print(green(_render("Updating virtualenv requirments"), True))
    _run("if [ ! -d %(app_virtualenv)s ];then mkvirtualenv %(app_id)s; fi;")
    with cd(_render("%(app_dir)s")):
        _run("workon %(app_id)s && pip install -r %(app_current_release)s/requirements.txt")

def link_release():
    """
    Update the current release symlinks
    """
    print(green(_render("Updating current and previous release symlinks"), True))
    _run('if [ -e %(app_previous_release)s ];then rm %(app_previous_release)s; fi;')
    _run('if [ -e %(app_current_release)s ];then mv %(app_current_release)s %(app_previous_release)s; fi;')
    _run('ln -s %(app_release_dir)s %(app_current_release)s')  
    
def check_dirs():
    """
    Create application specific directories
    """
    print(green(_render("Checking required directories are in place"), True))
    _mkdir(env.app_dir)
    _mkdir(env.app_releases_dir)
    _mkdir(env.app_config_dir)
    _mkdir(env.app_shared_dir)
    _mkdir(env.app_cache_dir)
    _mkdir(env.app_var_dir)
    _mkdir(env.app_run_dir)
    _mkdir(env.app_log_dir)

def check_symlinks():
    """
    Check to make sure all symbolic links are in place
    """
    print(green(_render("Checking required symlinks are in place"), True))
    env.server_nginx_conf = _render("%(server_nginx_config_dir)s/sites-enabled/%(app_id)s")
    _sudo("if [ ! -e %(server_nginx_conf)s ];then ln -s %(app_instance_dir)s/nginx.conf %(server_nginx_conf)s; fi;")
    env.server_uwsgi_conf = _render("%(server_uwsgi_config_dir)s/apps-enabled/%(app_id)s")
    _sudo("if [ ! -e %(server_uwsgi_conf)s ];then ln -s %(app_instance_dir)s/uwsgi.yaml %(server_uwsgi_conf)s; fi;")

def deploy():
    """
    Deploy the application
    """
    print(green(_render("Deploying application to %(host_string)s"), True))
    test()
    build()
    check_dirs()
    upload_release()
    link_release()
    upload_configuration()
    update_virtualenv()
    check_symlinks()
    stop_nginx()
    restart_uwsgi()
    start_nginx()
    clean()

def create_instance():
    """
    Creates an EC2 Instance
    """
    print(yellow("Creating EC2 instance"))
    conn = boto.connect_ec2(env.ec2_key, env.ec2_secret)
    image = conn.get_all_images(env.ec2_amis.split(","))
    
    reservation = image[0].run(1, 1, env.ec2_keypair, env.ec2_secgroups,
        instance_type=env.ec2_instancetype)
    instance = reservation.instances[0]
    time.sleep(3)
    conn.create_tags([instance.id], {"Name":env.server_tag})
    
    while instance.state == u'pending':
        print(yellow("Instance state: %s" % instance.state))
        time.sleep(10)
        instance.update()

    print(green("Instance state: %s" % instance.state))
    print(green("Public dns: %s" % instance.public_dns_name))
    
    return instance.public_dns_name

def uwsgi(command):
    """
    Run a uWSGI command through uwsg-manager
    """
    _sudo('uwsgi-manager %s %s' % (command, env.app_id))
    
def start_uwsgi():
    """
    Start the application's uWSGI process
    """
    uwsgi('-s')
    
def stop_uwsgi():
    """
    Stop the application's uWSGI process
    """
    uwsgi('-s')
    
def restart_uwsgi():
    """
    Restart the app's uWSGI process
    """
    uwsgi('-R')

def nginx(command):
    _sudo('/etc/init.d/nginx %s' % command, shell=False, pty=False)
    
def restart_nginx():
    """
    Restart nginx
    """
    nginx('restart')
    
def start_nginx():
    """
    Start nginx
    """
    nginx('start')
    
def stop_nginx():
    """
    Stop nginx
    """
    nginx('stop')  

def _oven():
    """
    Cooks the recipe. 
    """
    for ingredient in recipe:
        try: print(yellow(ingredient['message']))
        except KeyError: pass
        globals()["_" + ingredient['action']](ingredient['params'])
        
def _local(params, capture=False):
    """
    Runs a local command
    """
    return local(_render(params), capture=capture)
        
def _apt(params):
    """
    Runs apt-get install commands
    """
    for pkg in params:
        _sudo("apt-get install -qq %s" % pkg)


def _pip(params):
    """
    Runs pip install commands
    """
    for pkg in params:
        _sudo("pip install %s" % pkg)


def _run(params):
    """
    Runs command with active user
    """
    run(_render(params))


def _sudo(params, shell=True, pty=True):
    """
    Run command as root
    """
    sudo(_render(params), shell=shell, pty=pty)

def _put(params):
    """
    Moves a file from local computer to server
    """
    put(_render(params['file']), _render(params['destination']))


def _render(template, context=env):
    """
    Does variable replacement
    """
    return template % context


def _write_to(string, path):
    """
    Writes a string to a file on the server
    """
    return "echo '" + string + "' > " + path


def _append_to(string, path):
    """
    Appends to a file on the server
    """
    return "echo '" + string + "' >> " + path

def _mkdir(dir):
    """
    Create a directory if it doesn't exist
    """
    run('if [ ! -d %s ]; then mkdir -p %s; fi;' % (dir, dir))
    