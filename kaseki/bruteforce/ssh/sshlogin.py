import paramiko
from typing import Union
import multiprocessing as mp
import queue as q
from termcolor import cprint
from time import sleep

from kaseki.bruteforce.target import SSHTarget, Target
from kaseki.utils.queuecontent import Signal, QueueData

class SSHLogin:
    
    def __init__(self, target: Target, password: str, results_queue: Union[q.Queue, mp.Queue], max_attempts: int = 10):
        self.target = target
        self.password = password
        self.results_queue = results_queue
        self.max_attempts = max_attempts
        self.stop_flag = False
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def start(self) -> None:
        attempts = 0
        result = QueueData(Signal.Blank, None)
        
        while not self.stop_flag:
            try:
                self.client.connect(
                    hostname=self.target.hostname,
                    port=self.target.port,
                    username=self.target.username,
                    password=self.password,
                    timeout=10
                )
                result = QueueData(Signal.Success, self.password)
                # cprint(f"[+] Successful login with password: {self.password}", "cyan")
                break
            
            except paramiko.ssh_exception.AuthenticationException:
                result = QueueData(Signal.Failed, self.password)
                # cprint(f"[-] Authentication failed for password: {self.password}", "red")
                break
            
            except paramiko.ssh_exception.SSHException as e:
                attempts += 1
                # cprint(f"[SSHLogin] Attempting again with password {self.password} (Attempt {attempts}/{self.max_attempts})", "cyan")
                
                if attempts >= self.max_attempts:
                    # cprint(f"[+] Maximum attempts reached for password {self.password}. Sending retry signal.", "cyan")
                    result = QueueData(Signal.Retry, self.password)
                    break
                
                sleep(1)  # Wait before retrying

        # Ensure client is closed in any case
        try:
            self.client.close()
        except Exception as e:
            cprint(f"[ERROR] Failed to close SSH client: {e}", "red")
        
        self.results_queue.put(result)
        return
                    
    def stop(self) -> None:
        self.stop_flag = True
