from kaseki.bruteforce.protocol import Protocol

class Target:
    """
    Represents the details of the target server for brute-force attempts.

    Attributes:
        hostname (str): The hostname or IP address of the server.
        username (str): The username for login attempts.
        verbose (bool): Controls detailed logging output.
    """

    def __init__(
        self, 
        hostname: str = "localhost", 
        username: str = "root", 
        verbose: bool = False,
        port: int = 0
    ):
        """
        Initializes a Target instance.

        Args:
            hostname (str): The hostname or IP address of the server.
            username (str): The username for login attempts.
            verbose (bool): If True, enables detailed logging output.
        """
        self.hostname = hostname
        self.username = username
        self.verbose = verbose
        self.protocol: Protocol = Protocol(port) if port else Protocol()

        
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(hostname={self.hostname}, username={self.username}, "
                f"protocol={self.protocol}, verbose={self.verbose})")

    def __str__(self) -> str:
        return f"Target(hostname={self.hostname}, username={self.username})"

__all__ = ['Target']
