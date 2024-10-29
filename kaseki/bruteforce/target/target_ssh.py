from kaseki.bruteforce.protocol import SSH
from . import TCPTarget

class SSHTarget(TCPTarget):
    """
    Represents an SSH target for brute-force login attempts.

    Attributes:
        hostname (str): The hostname or IP address of the SSH server.
        username (str): The username for SSH login.
        port (int): The port number for SSH, defaults to 22.
        verbose (bool): Controls detailed logging output.
        protocol (SSH): The SSH protocol object associated with this target.
    """

    def __init__(self, hostname: str = "localhost", username: str = "root", port: int = 22, verbose: bool = False):
        super().__init__(hostname, username, verbose)
        self.protocol: SSH = SSH(port) if port else SSH()
    
    # @property 
    # def protocol(self) -> SSH:
    #     """Returns the SSH protocol instance."""
    #     return self._protocol
    
    def __str__(self) -> str:
        return "SSHTarget"

__all__ = ['SSHTarget']
