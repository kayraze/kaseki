from . import TCP

class FTP(TCP):
    
    def __init__(self, port:int=21):
        super().__init__(port)
    
    def __str__(self) -> str:
        return "FTP"

__all__ = ['FTP']
