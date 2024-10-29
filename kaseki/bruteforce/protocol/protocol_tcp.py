from .protocol import Protocol

class TCP(Protocol):
    
    def __init__(self, port:int=80):
        super().__init__(port)
    
    def __str__(self) -> str:
        return "TCP"
    
    
__all__ = ['TCP']