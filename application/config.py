"""
Default configuration values. These are generally for running
locally with the built in webserver. Adding something here means
you should add it to the /etc/config.py.tmpl file and possibly
create a value in the rcfile.sample file.
"""

import os

ENVIRONMENT = 'development'

# Flask
SITE_NAME = 'Application'
SECRET_KEY = 'secretkey'
DEBUG = True
TESTING = False

# App 
HOST_SCHEME = 'http'
HOST_DOMAIN = '127.0.0.1'
HOST_PORT = 5000

# Flask-Cache
CACHE_TYPE = 'filesystem'
CACHE_DIR = '%s/cache' % os.getcwd()
CACHE_DEFAULT_TIMEOUT = 60 * 60 * 24