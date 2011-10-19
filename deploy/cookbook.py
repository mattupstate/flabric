recipe = [

  {"action":"sudo", "params":'echo "deb http://nginx.org/packages/ubuntu/ lucid nginx" | sudo tee --append /etc/apt/sources.list'},
  {"action":"sudo", "params":'echo "deb-src http://nginx.org/packages/ubuntu/ lucid nginx" sudo tee --append /etc/apt/sources.list',
    "message": "Adding nginx repository info to Ubuntu"},
          
  {"action":"sudo", "params":"apt-get update -qq",
    "message":"Updating apt-get"},
  
  {"action":"apt",
    "params":["mysql-client", "libmysqlclient-dev", "memcached", "git", "nginx-full", "libxml2-dev",
      "python-setuptools", "python-dev", "build-essential", "python-pip", "python-mysqldb"],
    "message":"Installing apt-get packages"},
  
  {"action":"pip", "params":["virtualenv", "virtualenvwrapper", 
                             "http://projects.unbit.it/downloads/uwsgi-latest.tar.gz",
                             "https://github.com/mattupstate/uWSGI-Manager/tarball/latest"],
    "message":"Installing pip packages"},
          
  {"action":"sudo", "params":"wget -O /etc/init.d/uwsgi https://github.com/mattupstate/ubuntu-scripts/raw/master/etc/init.d/uwsgi", 
    "message":"Installing uWSGI script"},
  {"action":"sudo", "params":"chmod +x /etc/init.d/uwsgi"},
  {"action":"sudo", "params":"/usr/sbin/update-rc.d -f uwsgi defaults"},
            
  {"action":"sudo", "params":"mkdir -p %(server_uwsgi_config_dir)s/apps-available", "message":"Creating uWSGI config folders" },
  {"action":"sudo", "params":"mkdir -p %(server_uwsgi_config_dir)s/apps-enabled", },
  
  {"action":"run", "params":"mkdir %(server_virtualenv_dir)s", "message":"Configuring virtualenvwrapper"},
  {"action":"run", "params":"echo 'export WORKON_HOME=%(server_virtualenv_dir)s' >> %(server_user_home_dir)s/.profile"},
  {"action":"run", "params":"echo 'source /usr/local/bin/virtualenvwrapper.sh' >> %(server_user_home_dir)s/.profile"},
  {"action":"run", "params":"source %(server_user_home_dir)s/.profile"},
  
  {"action":"sudo", "params":"rm %(server_nginx_config_dir)s/sites-enabled/default"},
  {"action":"sudo", "params":"/etc/init.d/nginx start"},
            
]