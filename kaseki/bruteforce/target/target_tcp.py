from . import Target
from kaseki.bruteforce.protocol import TCP

class TCPTarget(Target):
    """
    Represents a TCP target for brute-force login attempts.

    Attributes:
        hostname (str): The hostname or IP address of the TCP server.
        username (str): The username for TCP login.
        port (int): The port number for TCP communication, defaults to 80.
        verbose (bool): Controls detailed logging output.
        protocol (TCP): The TCP protocol object associated with this target.
    """

    def __init__(self, hostname: str = "localhost", username: str = "root", port: int = 80, verbose: bool = False):
        """
        Initializes a TCPTarget instance.

        Args:
            hostname (str): The hostname or IP address of the TCP server.
            username (str): The username for TCP login.
            port (int): The port number for TCP communication.
            verbose (bool): If True, enables detailed logging output.
        """
        super().__init__(hostname, username, verbose)
        self.protocol: TCP = TCP(port) if port else TCP()
        

    def __str__(self) -> str:
        return "TCPTarget"
    
__all__ = ['TCPTarget']
