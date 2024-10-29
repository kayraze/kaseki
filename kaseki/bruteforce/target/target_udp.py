from kaseki.bruteforce.protocol import UDP  # Ensure you have a UDP class similar to TCP
from . import Target

class UDPTarget(Target):
    
    def __init__(self, hostname: str = "localhost", username: str = "root", port: int = 53, verbose: bool = False):
        """
        Initializes a UDPTarget instance.

        Args:
            hostname (str): The hostname or IP address of the target server.
            username (str): The username for login attempts (if applicable).
            port (int): The port number for UDP, defaults to 53 (DNS).
            verbose (bool): If True, enables detailed logging output.
        """
        super().__init__(hostname, username, verbose)
        self.protocol: UDP = UDP(port) if port else UDP()  # Assuming you have a UDP class in protocols

    
    def __str__(self) -> str:
        """Returns a string representation of the UDPTarget."""
        return f"UDPTarget(hostname={self.hostname}, username={self.username}, port={self.protocol.port})"

__all__ = ['UDPTarget']
