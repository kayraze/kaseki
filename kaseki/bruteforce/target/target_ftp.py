from . import TCPTarget
from kaseki.bruteforce.protocol import FTP

class FTPTarget(TCPTarget):
    """
    Represents an FTP target for brute-force login attempts.

    Attributes:
        hostname (str): The hostname or IP address of the FTP server.
        username (str): The username for FTP login.
        port (int): The port number for FTP, defaults to 21.
        verbose (bool): Controls detailed logging output.
        protocol (FTP): The FTP protocol object associated with this target.
    """

    def __init__(self, hostname: str = "localhost", username: str = "root", port: int = 21, verbose: bool = False):
        super().__init__(hostname, username, verbose)
        self.protocol: FTP = FTP(port) if port else FTP()

    def __str__(self) -> str:
        return "FTPTarget"

__all__ = ['FTPTarget']
