from abc import ABC, abstractmethod
from typing import Optional

class Protocol:
    
    def __init__(self, port: int = 0):
        self.port = port

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(port={self.port})"
    
    def __str__(self) -> str:
        return "Protocol"

__all__ = ['Protocol']
