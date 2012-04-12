from __future__ import with_statement
import time, types, tempfile
from cuisine import *
from fabric.api import *
from fabric.colors import *


class Server(object):
    
    def reboot(self):
        raise NotImplementedError()

    def setup(self):
        raise NotImplementedError()

    def restart(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

class ApplicationContext(object):

    def __init__(self, name, user=None):
        self.name = name
        self.user = user

    def restart(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

def _getattr(objstr):
    parts = objstr.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m

def _get_server():
    return _getattr(env.server_type)()

def _get_app_context():
    return _getattr(env.server_appcontext)()

def render(obj):
        """Convienently render strings with the fabric context"""
        def get_v(v):
            return v % env if isinstance(v, basestring) else v

        if isinstance(obj, types.StringType):
            return obj % env
        elif isinstance(obj, types.TupleType) or isinstance(obj, types.ListType):
            rv = []
            for v in obj:
                rv.append(get_v(v))
        elif isinstance(obj, types.DictType):
            rv = {}
            for k, v in obj.items():
                rv[key] = get_v(v)
        return rv

def create_server():
    """Create a server instance and set it up"""
    start_time = time.time()
    print(green("Creating new server..."))
    provider = _getattr('flabric.providers.%s' % env.server_provider)()
    env.host_string = provider.create_instance()
    print(green("Waiting 30 seconds for server to boot..."))
    time.sleep(30)
    setup_server()
    end_time = time.time()
    print(green('*' * 100))
    print(green("Server created in %f minutes!" % ((end_time - start_time) / 60)))
    print(green("Change the value of host_string in your rcfile to:"))
    print(green(env.host_string))
    print(green('*' * 100))

class app_bundle(object):

    def __enter__(self):
        env.local_bundle = tempfile.mkstemp(suffix='.tar')[1]
        run_local(render('git archive --format=tar %(git_branch)s > %(local_bundle)s'))

    def __exit__(self, *args, **kwargs):
        os.unlink(env.local_bundle)
        env.local_bundle = None

def setup_server():
    """Setup the sever"""
    _get_server().setup()

def reboot_server():
    """Reboot the sever"""
    _get_server().reboot()

def restart_server():
    """Restart the sever"""
    _get_server().restart()

def start_server():
    """Start the sever"""
    _get_server().start()

def stop_server():
    """Stop the sever"""
    _get_server().stop()

def create_app_context():
    """Create an app context"""
    _get_server().create_app_context(_get_app_context())

def deploy():
    upload_app()
    upload_config()
    #tag_deployment()
    restart_server()

def upload_app():
    """upload_app"""
    with app_bundle():
        _get_server().upload_app(_get_app_context())

def upload_config():
    """upload configuration"""
    _get_server().upload_config(_get_app_context())
