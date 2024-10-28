from abc import abstractmethod
from termcolor import cprint
from time import sleep
import queue
import multiprocessing
from typing import Union, Any, Generator

from .queuecontent import QueueData, Signal


class PasswordProducer:
    """
    A class that produces password data from a file, queuing each password for processing.
    Reads passwords from a specified file and places them in a queue for further use by a consumer.

    Attributes:
        password_filename (str): The name of the file containing passwords.
        passwords_queue (Union[queue.Queue, multiprocessing.Queue]): Queue to store the passwords.
        termination_value (Any): Value indicating the termination signal for consumers.
        delay (Union[int, float]): Delay between adding passwords to the queue, simulating processing time.
        stop_flag (bool): Flag indicating if the producer should stop.
        verbose (bool): If True, enables verbose logging output.
    """
    
    def __init__(
            self, 
            password_filename: str, 
            passwords_queue: Union[queue.Queue[QueueData], multiprocessing.Queue[QueueData]], 
            termination_value: Any = None, 
            delay: Union[int, float] = 0,
            verbose: bool = True
        ):
        self.password_filename = password_filename
        self.passwords_queue = passwords_queue
        self.termination_value = termination_value
        self.delay = delay
        self.stop_flag = False
        self.verbose = verbose

    def yield_data(self) -> Generator[str, None, None]:
        """
        Yields each line from the file specified by `password_filename`.

        Reads the file line by line, allowing each line (representing a password) to be 
        processed individually, suitable for handling large files.

        Yields:
            str: Each line of the password file as a password string.
        """
        with open(self.password_filename, 'r') as file:
            for line in file:
                yield line

    def produce(self, delay: Union[int, float] = 0) -> None:
        """
        Reads passwords from a file and adds them to the `passwords_queue`.

        Each password is read from the file, stripped of extra whitespace, and then placed
        into the `passwords_queue` as `QueueData` with a `Data` signal. Once all passwords
        are added, a final `NoPasswordsLeft` signal is queued to inform consumers there
        are no more passwords available.

        Args:
            delay (Union[int, float]): Optional delay between queuing each password, defaults to 0.
        """
        passgen: Generator[str, None, None] = self.yield_data()  # Generator for iterating through passwords
        for password in passgen:
            password = password.strip()  # Remove trailing/leading whitespace
            if self.stop_flag:
                break  # Stop if stop flag is set

            # Enqueue password data with a Data signal
            self.passwords_queue.put(QueueData(
                Signal.Data,
                password
            ))
            sleep(delay)  # Delay to simulate processing time

        # Signal that no passwords are left in the file
        self.passwords_queue.put(QueueData(
            Signal.NoPasswordsLeft,
            None
        ))

        # Optional verbose output
        if self.verbose:
            cprint("[+] PasswordProducer successfully terminated", "yellow", attrs=["bold"])
        
        exit()  # Terminate the producer

    def stop(self) -> None:
        """
        Sets the `stop_flag`, allowing the producer to gracefully terminate.

        When `stop_flag` is True, the `produce` method will exit its loop and send a termination signal.
        """
        self.stop_flag = True


__all__ = ['PasswordProducer']