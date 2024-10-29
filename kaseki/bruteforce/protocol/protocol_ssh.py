from .protocol_tcp import TCP

class SSH(TCP):
    
    def __init__(self, port:int=22):
        self.port = port
    
    def __str__(self) -> str:
        return "SSH"

__all__ = ['SSH']