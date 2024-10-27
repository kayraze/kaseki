
class Target:
    """
    Represents the details of the target server for brute-force attempts.

    Attributes:
        hostname (str): The hostname or IP address of the SSH server.
        port (int): The port number for SSH, defaults to 22.
        username (Optional[str]): The username for SSH login.
        verbose (bool): Controls detailed logging output.
    """

    def __init__(
        self, 
        hostname: str = "localhost", 
        port: int=0, 
        username: str="root", 
        verbose: bool = False
    ):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.verbose = verbose
        
        
class SSHTarget(Target):
    
    pass

class FTPTarget(Target):
    
    pass