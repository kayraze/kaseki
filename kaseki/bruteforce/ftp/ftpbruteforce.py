from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union, Callable
import queue as q
import multiprocessing as mp
import threading as td
from time import sleep
from termcolor import cprint

from  kaseki.bruteforce.ftp.ftplogin import FTPLogin
from kaseki.utils.queuecontent import Signal, QueueData
from kaseki.bruteforce.target import Target, FTPTarget

class FTPBruteForcer:
    
    
    def __init__(
        self, 
        target: Target, 
        passwords_queue: Union[q.Queue, mp.Queue], 
        results_queue: Union[q.Queue, mp.Queue], 
        thread_n: int=0, 
        max_attempts:int=100
    ):
        self.target = target
        self.passwords_queue = passwords_queue
        self.results_queue = results_queue
        self.thread_n = thread_n
        self.max_attempts = max_attempts
        self.stop_flag: bool = False
        self.futures: list = []
        self.semaphore: td.Semaphore = td.Semaphore(thread_n)
        
    def get_brute_force_method(self) -> Callable:
        return self.threaded_bruteforce if self.thread_n > 0 else self.nonthreaded_bruteforce
    
    def start(self) -> None:
        bruteforce_method = self.get_brute_force_method()
        bruteforce_method()
        
    
    def nonthreaded_bruteforce(self) -> None:
        while not self.stop_flag:
            queuedata: QueueData = self.passwords_queue.get()
            signal: Signal = queuedata.signal
            
            if signal is Signal.NoPasswordsLeft:
                break
            
            password = queuedata.content
            
            ftp_login : FTPLogin = FTPLogin(
                self.target,
                password,
                self.results_queue,
                self.max_attempts
            )
            ftp_login.start()
    
    def threaded_bruteforce(self) -> None:
        
        try:
            with ThreadPoolExecutor(max_workers=self.thread_n) as executor:
                while not self.stop_flag:
                    queuedata: QueueData = self.passwords_queue.get()
                    signal: Signal = queuedata.signal
                    if signal is Signal.NoPasswordsLeft or signal is Signal.Success:
                        self.passwords_queue.put(signal)
                        break
                        
                    password = queuedata.content
                
                    self.semaphore.acquire()
                    if self.stop_flag:
                        break
                    ftp_login : FTPLogin = FTPLogin(
                        self.target,
                        password,
                        self.results_queue,
                        self.max_attempts
                    )
                    future = executor.submit(self.run_login, ftp_login)
                    self.futures.append(future)

                        
            self.wait_for_threads()
        except Exception as e:
            cprint(f"[ERROR] FTPBruteForcer: {e}", "red", attrs=["bold"])
                    
                    
    def wait_for_threads(self) -> None:
        for future in self.futures:
            try:
                future.result()  # This will block until the future is done
            except Exception as e:
                print(f"Error while waiting for future: {e}")
                
    def run_login(self, ftp_login):
        """Wrapper function to run ftp login and release semaphore."""
        try:
            if not self.stop_flag:
                ftp_login.start()  # Run the login attempt
        finally:
            self.semaphore.release()  # Ensure the semaphore is released after running

        
    def stop(self) -> None:
        self.stop_flag = True