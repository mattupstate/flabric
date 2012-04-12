from __future__ import with_statement
from cuisine import *
from fabric.api import env
from fabric.colors import *
from fabric.utils import puts
from fabric.contrib.console import confirm
from fabric.context_managers import cd, settings
from flabric import ApplicationContext as AppContext, render
from flabric.ubuntu import UbuntuServer
import os, flabric


class Server(UbuntuServer):
    """nginx, uWSGI and supervisor server"""

    def setup(self):
        with mode_sudo():
            group_ensure('admin')

            for u in [('ubuntu', '/home/ubuntu'),('supervisor', None)]:
                puts(green('Ensuring user: %s' % u[0]))
                user_ensure(u[0], home=u[1])

            group_user_ensure('admin', 'ubuntu')

            print(green("Updating /etc/sudoers"))
            file_update(
                '/etc/sudoers', 
                lambda _: text_ensure_line(_,
                    '%admin ALL=(ALL) ALL',
                    'ubuntu  ALL=(ALL) NOPASSWD:ALL'
            ))

            print(green("Adding your public key to ubuntu user"))
            ssh_authorize('ubuntu', file_local_read('~/.ssh/id_rsa.pub'))

            puts(green('Updating repository info for nginx'))
            file_update(
                '/etc/apt/sources.list', 
                lambda _: text_ensure_line(_,
                    'deb http://nginx.org/packages/ubuntu/ lucid nginx',
                    'deb-src http://nginx.org/packages/ubuntu/ lucid nginx'
            ))

            puts(green('Adding singing key for nginx'))
            keys = run('apt-key list')

            if not 'nginx' in keys:
                run('wget http://nginx.org/keys/nginx_signing.key')
                run('apt-key add nginx_signing.key')
            
            run('apt-get update -qq')
            
            for p in ['build-essential', 
                      'libmysqlclient-dev', 
                      'libxml2-dev', 
                      'libjpeg62-dev', 
                      'python-dev', 
                      'python-setuptools', 
                      'python-mysqldb', 
                      'python-pip',
                      'mysql-client', 
                      'git-core', 
                      'nginx']:
                puts(green('Installing: %s' % p))
                package_ensure(p)
            
            puts(green('Linking libraries'))
            for l in [('/usr/lib/x86_64-linux-gnu/libfreetype.so', 
                           '/usr/lib/libfreetype.so'),
                      ('/usr/lib/x86_64-linux-gnu/libz.so', 
                           '/usr/lib/libz.so'),
                      ('/usr/lib/x86_64-linux-gnu/libjpeg.so', 
                           '/usr/lib/libjpeg.so')]:
                file_link(l[0], l[1])
            
            for p in ['virtualenv', 
                      'virtualenvwrapper',
                      'supervisor',
                      'uwsgi']:
                puts(green('Installing: %s' % p))
                run('pip install %s' % p)
            
            puts(green('Configuring supervisor and nginx'))
            
            tdir = os.path.dirname(__file__)
            for f in [('/etc/supervisord.conf', 'supervisord.conf.tmpl'),
                      ('/etc/nginx/nginx.conf', 'nginx.conf.tmpl'),
                      ('/etc/init.d/supervisor', 'supervisor.tmpl')]:
                fn = f[0]
                contents = file_local_read(os.path.join(tdir, 'templates', f[1]))
                if not file_exists(fn):
                    file_write(fn, contents)
                else:
                    if confirm('The file %s already exists. '
                               'Do you want to overwrite it?' % fn):
                        file_update(fn, lambda _:contents)

            puts(green('Create supervisor config folder'))
            dir_ensure('/etc/supervisor')

            puts(green('Remove default nginx site'))
            run('rm /etc/nginx/conf.d/*')

            run('chmod +x /etc/init.d/supervisor')
            run('update-rc.d supervisor defaults')

        self.restart()
        puts(green('Server setup complete!'))
        puts(green('Add sites to nginx by linking configuration files in /etc/nginx/sites-enabled.'))
        puts(green('Add uWSGI processes to supervisor by linking configuration files in /etc/supervisor/apps-enabled.'))

    def restart(self):
        puts(green('Restarting server'))
        for c in ['nginx', 'supervisor']:
            sudo('/etc/init.d/%s restart' % c)

    def start(self):
        puts(green('Starting server'))
        for c in ['nginx', 'supervisor']:
            sudo('/etc/init.d/%s start' % c)

    def stop(self):
        puts(green('Stoping server'))
        for c in ['nginx', 'supervisor']:
            sudo('/etc/init.d/%s stop' % c)

    def create_app_context(self, ctx):
        with settings(user=ctx.user or env.user):
            puts(green('Creating app context under user: %s' % env.user))
            
            dot_profile = '/home/%s/.profile' % ctx.user
            file_ensure(dot_profile)
            file_update(
                dot_profile, 
                lambda _: text_ensure_line(_,
                    'WORKON_HOME=~/.virtualenv',
                    'source /usr/local/bin/virtualenvwrapper.sh'
            ))

            for d in ctx.required_dirs:
                dir_ensure(d)

            run('mkvirtualenv %s' % ctx.name)

    def upload_app(self, ctx):
        ctx.upload()

    def upload_config(self, ctx):
        with mode_sudo():
            for c in [(env.nginx_tmpl,'/etc/nginx/conf.d/%s'), 
                      (env.supervisor_tmpl, '/etc/supervisor/%s')]:
                fn = c[1] % ctx.name
                if file_exists(fn):
                    run('rm %s' % fn)
                file_write(fn, file_local_read(c[0]) % ctx.__dict__)


class ApplicationContext(AppContext):

    def __init__(self, name='default', user='ubuntu'):
        super(ApplicationContext, self).__init__(name, user)
        self.virtualenv = '/home/%s/.virtualenv/%s' % (self.user, self.name)
        self.root_dir = '/home/%s/%s' % (self.user, self.name)
        self.src_dir = '%s/src' % self.root_dir
        self.log_dir = '%s/log' % self.root_dir
        self.run_dir = '%s/run' % self.root_dir

    @property
    def required_dirs(self):
        return [self.root_dir, self.src_dir, self.log_dir, self.run_dir]

    def upload(self):
        with settings(user=self.user or env.user):
            env.remote_bundle = os.path.join('/tmp', os.path.basename(env.local_bundle))
            
            file_upload(env.remote_bundle, env.local_bundle)
            
            run('rm -rf %s' % self.src_dir)
            dir_ensure(self.src_dir)
            
            with cd(self.src_dir):
                run(render('tar -xvf %(remote_bundle)s'))