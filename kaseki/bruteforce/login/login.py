# login.py
from typing import Union
import queue as q
import multiprocessing as mp
from kaseki.utils import QueueData, ConcurrentQueue
from kaseki.bruteforce.target import Target

class Login:
    def __init__(self, target: Target, password: str, results_queue: ConcurrentQueue):
        self.target = target
        self.password = password
        self.results_queue = results_queue

    def start(self) -> None:
        pass

__all__ = ['Login']
