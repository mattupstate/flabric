from __future__ import with_statement
from cuisine import *
from fabric.api import env
from fabric.colors import *
from fabric.utils import puts
from fabric.context_managers import cd, settings, prefix
from flabric import ApplicationContext as AppContext
from flabric.ubuntu import UbuntuServer
import os, flabric


class Server(UbuntuServer):
    """nginx, uWSGI and supervisor server"""

    def setup(self):
        with mode_sudo():
            group_ensure('admin')

            for u in [('ubuntu', '/home/ubuntu')]:
                puts(green('Ensuring user: ' + u[0]))
                user_ensure(u[0], home=u[1])

            group_user_ensure('admin', 'ubuntu')

            puts(green("Updating /etc/sudoers"))
            file_update(
                '/etc/sudoers', 
                lambda _: text_ensure_line(_,
                    '%admin ALL=(ALL) ALL',
                    'ubuntu  ALL=(ALL) NOPASSWD:ALL'
            ))

            puts(green("Adding your public key to ubuntu user"))
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
                puts(green('Installing: ' + p))
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
                puts(green('Installing: ' + p))
                run('pip install ' + p)
            
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
                    file_update(fn, lambda _:contents)

            puts(green('Create supervisor config folder'))
            dir_ensure('/etc/supervisor')

            run('chmod +x /etc/init.d/supervisor')
            run('update-rc.d supervisor defaults')

            run('/etc/init.d/supervisor start')
        
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
        with settings(user=ctx.user):
            puts(green('Creating app context under user: ' + env.user))

            tdir = os.path.dirname(__file__)
            
            for f in ['bashrc', 'bash_profile', 'profile']:
                lfn = os.path.join(tdir, 'templates', '%s.tmpl' % f)
                contents = file_local_read(lfn) % ctx.__dict__
                rfn = '/home/%s/.%s' % (ctx.user, f)
                file_ensure(rfn, owner=ctx.user, group=ctx.user)
                file_update(rfn, lambda _:contents)
            
            dir_ensure('/home/%s/sites' % ctx.user)
            
            for d in ctx.required_dirs:
                dir_ensure(d)

    def upload_app(self, ctx):
        ctx.pre_upload()

        with settings(user=ctx.user):
            env.remote_bundle = '/tmp/' + os.path.basename(env.local_bundle)
            
            file_upload(env.remote_bundle, env.local_bundle)
            
            run('rm -rf ' + ctx.src_dir)
            dir_ensure(ctx.src_dir)
            
            with cd(ctx.src_dir):
                run('tar -xvf ' + env.remote_bundle)

        ctx.post_upload()

    def upload_config(self, ctx):
        with settings(user=ctx.user):
            for c in [(env.nginx_template,'nginx'), 
                      (env.supervisor_template, 'supervisor')]:
                
                fn = '%s/%s.conf' % (ctx.etc_dir, c[1])
                contents = file_local_read(c[0]) % ctx.__dict__
                
                if file_exists(fn):
                    file_update(fn, lambda _:contents)
                else:
                    file_write(fn, contents)

        with mode_sudo():
            for c in [('/etc/nginx/conf.d', 'nginx'), 
                      ('/etc/supervisor', 'supervisor')]:
                source = '%s/%s.conf' % (ctx.etc_dir, c[1])
                destination = '%s/%s.conf' % (c[0], ctx.name)

                if file_exists(destination) and (not file_is_link(destination)):
                    run('rm ' + destination)
                
                file_link(source, destination)


class ApplicationContext(AppContext):

    def __init__(self, name='default', user='ubuntu'):
        super(ApplicationContext, self).__init__(name, user)
        self.virtualenv = '/home/%s/.virtualenv/%s' % (self.user, self.name)
        self.root_dir = '/home/%s/sites/%s' % (self.user, self.name)
        self.releases_dir = self.root_dir + '/releases'
        self.src_dir = self.releases_dir + '/current'
        self.etc_dir = self.root_dir + '/etc'
        self.log_dir = self.root_dir + '/log'
        self.run_dir = self.root_dir + '/run'

    @property
    def required_dirs(self):
        return [self.root_dir, self.releases_dir, self.src_dir, 
                self.etc_dir, self.log_dir, self.run_dir]

    def pre_upload(self):
        pass

    def post_upload(self):
        run('rmvirtualenv ' + self.name)
        run('mkvirtualenv ' + self.name)
        with settings(user=self.user):
            with cd(self.src_dir):
                with prefix('workon ' + self.name):
                    run('pip install -r requirements.txt')