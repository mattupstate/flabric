from __future__ import with_statement
from cuisine import *
from fabric.colors import *
from fabric.utils import puts
from fabric.contrib.console import confirm
from flabric import Server
import os, flabric

class ubuntu_server(Server):
    def reboot(self):
        sudo('reboot')

class nginx_uwsgi_supervisor(ubuntu_server):
    """nginx, uWSGI and supervisor recipe"""

    def setup(self):
        with mode_sudo():
            puts(green('Adding `supervisor` user'))
            user_ensure('supervisor')

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

            puts(green('Ensuring required directories'))
            for d in ['/etc/supervisor/apps-available',
                      '/etc/supervisor/apps-enabled',
                      '/etc/nginx/sites-available',
                      '/etc/nginx/sites-enabled']:
                dir_ensure(d)

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