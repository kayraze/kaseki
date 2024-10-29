import paramiko
from typing import Union
import multiprocessing as mp
import queue as q
from termcolor import cprint
from time import sleep

from kaseki.bruteforce.protocol import Protocol
from kaseki.bruteforce.login import Login
from kaseki.bruteforce.target import SSHTarget
from kaseki.utils import Signal, QueueData, ConcurrentQueue

class SSHLogin(Login):
    
    def __init__(self, target: SSHTarget, password: str, results_queue: ConcurrentQueue):
        self.target = target
        self.password = password
        self.results_queue = results_queue
        self.stop_flag = False
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def start(self) -> None:
        result: Signal = Signal.Blank
        
        while not self.stop_flag:
            try:
                self.client.connect(
                    hostname=self.target.hostname,
                    port=self.target.protocol.port,
                    username=self.target.username,
                    password=self.password,
                    timeout=10
                )
                result = Signal.Success
                break
            
            except paramiko.ssh_exception.AuthenticationException:
                result = Signal.Failed
                break
            
            except paramiko.ssh_exception.SSHException as e:
                sleep(1)
                continue
        try:
            self.client.close()
        except Exception as e:
            cprint(f"[ERROR] Failed to close SSH client: {e}", "red")
        
        self.results_queue.put(QueueData(
            result,
            self.password
        ))
        return
                    
    def stop(self) -> None:
        self.stop_flag = True


__all__ = ['SSHLogin']
