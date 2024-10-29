from __future__ import annotations

import enum
from typing import Any, Generic, TypeAlias, Union, TypeVar, Optional, cast, Type
import multiprocessing as mp
import  queue as q


class Signal(enum.Enum):
    """
    Enum representing various signals that can be used for message passing
    between different components in a queue-based system. These signals indicate
    different states, actions, or instructions, and can be used to control
    flow and trigger specific behaviors within consumers.

    Signals:
        Normal: General purpose signal.
        Finished: Indicates completion of a task.
        Failed: Indicates a failed attempt or operation.
        Success: Signals that an operation was successful.
        Waiting: Signifies that a process is waiting for some condition.
        Blank: A placeholder signal.
        Data: Represents that data is available.
        Error: Indicates an error condition.
        Retry: Suggests retrying an operation.
        NoPasswordsLeft: Indicates there are no more passwords to process.
        StopConsumer: Command signal to stop a consumer.
        Forward: Signal to forward data or continue processing.
        Stop: General stop signal to halt an operation.
        Ignore: Signals to ignore an item or continue without action.
    """
    
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


class QueueData:
    """
    Class representing an object that can be pushed into a queue with an
    associated signal and content. Provides a structure for queue messages
    to help control workflow, error handling, or message passing in producer-
    consumer models.

    Attributes:
        signal (Signal): A signal that describes the type or purpose of this message.
        content (Any): The data or message associated with this queue item.
    
    Args:
        signal (Signal): The signal indicating the type or purpose of the message.
        content (Any): Any data or message content to be passed along with the signal.
    """

    def __init__(self, signal: Signal, content: Any):
        self.signal: Signal = signal  # Type of signal, e.g., Data, Success, etc.
        self.content: Any = content   # Associated data or message content

    def __str__(self) -> str:
        """
        Returns a string representation of the QueueData object, including
        its signal and content for easy reading and debugging.

        Returns:
            str: A string in the format "Signal: Content".
        """
        return f"{self.signal}: {self.content}"
    


DataQueue = Type["q.Queue[QueueData]"]
MPDataQueue = Type["mp.Queue[QueueData]"]

# You can define a type alias for easier use
ConcurrentQueue = Union["q.Queue[QueueData]", "mp.Queue[QueueData]"]
# ConcurrentQueue = Union[DataQueue, MPDataQueue]


__all__ = ['Signal', 'QueueData', 'ConcurrentQueue']