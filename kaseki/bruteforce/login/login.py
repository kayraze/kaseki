from kaseki.bruteforce import *
from typing import Union
import queue as q
import multiprocessing as mp

from kaseki.bruteforce.target import Target

class Login:
    
    def __init__(self, target: Target, password: str, results_queue: Union[q.Queue, mp.Queue], max_attempts: int):
        pass
    
    def start(self) -> None:
        pass


__all__ = ['Login']