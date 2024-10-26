import enum
from typing import Any

class Signal(enum.Enum):
    """ A base class for representing any type of signal """

    Normal = enum.auto()
    Finished = enum.auto()
    Failed = enum.auto()
    Success = enum.auto()
    Waiting = enum.auto()
    Blank = enum.auto()
    Data = enum.auto() 
    Error = enum.auto()
    Retry = enum.auto()
    NoPasswordsLeft = enum.auto()
    StopConsumer = enum.auto()
    Forward = enum.auto()
    Stop = enum.auto()
    Ignore = enum.auto()
# class Password(Signal):
#     """ A class to represent any signal about passwords"""


class QueueData:
    """A base class for objects to be pushed 
    in to the queue.
    
    args:
        signal (Signal): A signal can be used for any purposes
        content (any): A message or data of this object
    """

    def __init__(self, signal: Signal, content: Any):
        self.signal: Signal  = signal
        self.content: Any = content

    def __str__(self):
        return f"{self.signal}: {self.content}"
    