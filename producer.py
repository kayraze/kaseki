from abc import abstractmethod
from termcolor import cprint
from time import sleep
import queue
import multiprocessing
import queuecontent
from typing import Union, Any

class DataQueuer:

    def __init__(self, queue):
        self.queue = queue

    @abstractmethod
    def yield_data(self):
        pass

    def produce(self):
        """Recieves yielded passwords and puts it in the queue"""
        data_generator = self.yield_data()
        for data in data_generator:
            self.queue.put(data)

class FileContentQueuer(DataQueuer):
    """
    A base class for reading a file line by line and pushing to the queue

    Attributes:
        filename (str): the filename to be read line by line
        queue (queue.Queue): queue for putting the read lines
    """

    def __init__(self, filename, queue):

        self.filename = filename
        self.queue = queue

    def yield_data(self):
        """Yields each line of the object's file"""
        with open(self.filename, 'r') as file:
            for line in file:
                yield line

    def produce(self):
        """Recieves yielded passwords and puts it in the queue"""
        data_generator = self.yield_data()
        for data in data_generator:
            if self.stop_flag:
                break
            self.queue.put(data)

    def put(self, value: Any, timeout=0) -> None:
        self.queue.put(
            value,
            timeout=timeout,
        )

    def stop(self):
        self.stop_flag = True


class PasswordProducer(FileContentQueuer):

    """
    A clsss for pushing passwords in a queue

    args:
        password_filename (str)
    """

    def __init__(
            self, 
            password_filename: str, 
            passwords_queue: Union[queue.Queue, multiprocessing.Queue], 
            termination_value: Any=None, 
            delay:Union[int, float]=0
        ):
        self.password_filename: str = password_filename
        self.passwords_queue: Union[queue.Queue, multiprocessing.Queue] = passwords_queue
        self.termination_value: Any = termination_value
        self.delay: Union[int, float] = delay
        self.stop_flag: bool = False


    def yield_data(self):
        """Yields each line of the object's file"""
        with open(self.password_filename, 'r') as file:
            for line in file:
                yield line


    def produce(self, delay=0):
        """Reads passwords from a file and adds them to the password queue."""
        passgen = self.yield_data()
        for password in passgen:
            password = password.strip()
            if self.stop_flag:
                break

            self.put(queuecontent.QueueData(
                queuecontent.Signal.Data,
                password
            ))
            sleep(delay)

        self.put(queuecontent.QueueData(
            queuecontent.Signal.NoPasswordsLeft,
            None,
        ))
        cprint("[+] PasswordProducer successfuly terminated", "yellow", attrs=["bold"])
        exit()

