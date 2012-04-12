from cuisine import sudo
from flabric import Server

class UbuntuServer(Server):
    def reboot(self):
        sudo('reboot')