from .protocol import Protocol


class UDP(Protocol):
    
    def __init__(self, port:int=53):
        super().__init__(port)
    
    def __str__(self) -> str:
        return "UDP"
    
    
__all__ = ['UDP']