from abc import abstractmethod
from termcolor import cprint
from time import sleep
import queue  # Ensure this is the standard library's queue
import multiprocessing
from typing import Union, Any, Generator

from .queuecontent import QueueData, Signal, ConcurrentQueue

class PasswordProducer:
    """
    A class that produces password data from a file, queuing each password for processing.
    Reads passwords from a specified file and places them in a queue for further use by a consumer.
    """
    
    def __init__(
            self, 
            password_filename: str, 
            passwords_queue: ConcurrentQueue,  # Removed subscript to prevent errors
            termination_value: Any = None, 
            delay: Union[int, float] = 0,
            verbose: bool = False
        ):
        self.password_filename = password_filename
        self.passwords_queue = passwords_queue
        self.termination_value = termination_value
        self.delay = delay
        self.stop_flag = False
        self.verbose = verbose

    def yield_data(self) -> Generator[str, None, None]:
        """Yields each line from the file specified by `password_filename`."""
        with open(self.password_filename, 'r') as file:
            for line in file:
                yield line.strip()  # Strip whitespace while yielding

    def produce(self) -> None:
        """Reads passwords from a file and adds them to the `passwords_queue`."""
        for password in self.yield_data():
            if self.stop_flag:
                break  # Stop if stop flag is set

            # Enqueue password data with a Data signal
            self.passwords_queue.put(QueueData(
                Signal.Data,
                password
            ))
            sleep(self.delay)  # Delay to simulate processing time

        # Signal that no passwords are left in the file
        self.passwords_queue.put(QueueData(
            Signal.NoPasswordsLeft,
            None
        ))

        # Optional verbose output
        if self.verbose:
            cprint("[+] PasswordProducer successfully terminated", "yellow", attrs=["bold"])

    def stop(self) -> None:
        """Sets the `stop_flag`, allowing the producer to gracefully terminate."""
        self.stop_flag = True

__all__ = ['PasswordProducer']
