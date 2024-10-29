from termcolor import cprint
from typing import Union, Callable, List, Type
import queue as q
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, Future
import threading as td
from time import sleep

from .target import Target, SSHTarget,FTPTarget
from .login import Login, SSHLogin, FTPLogin
from .protocol import Protocol
from kaseki.utils import QueueData, Signal, ConcurrentQueue
# from kaseki.bruteforce.bruteforceutils.utils_login import get_login_type_with_target

def get_login_type_with_target(target: Target) -> Type[Login]:
    if isinstance(target, SSHTarget):
        return SSHLogin
    elif isinstance(target, FTPTarget):
        return FTPLogin
    return Login

class BruteForcer:
    
    def __init__(
        self, 
        target: Target,
        passwords_queue: ConcurrentQueue, 
        results_queue: ConcurrentQueue,
        thread_n: int=0, 
        verbose:bool = False
    ):
        self.target = target
        self.passwords_queue = passwords_queue
        self.results_queue = results_queue
        self.thread_n = thread_n
        self.verbose = verbose
        
        self.stop_flag: bool = False
        self.futures: List[Future[None]] = []
        self.semaphore: td.Semaphore = td.Semaphore(thread_n)
        self.running_n: int = 0
        self.thread_lock: td.Lock = td.Lock()
        
        self.protocol: Protocol = target.protocol
        self.login: Type[Login] = get_login_type_with_target(target)
        
        
        
    def get_brute_force_method(self) -> Callable[[], None]:
        return self.threaded_bruteforce if self.thread_n > 0 else self.nonthreaded_bruteforce
    
    def start(self) -> None:
        bruteforce_method = self.get_brute_force_method()
        bruteforce_method()
        return        
    
    

    
    def nonthreaded_bruteforce(self) -> None:
        while not self.stop_flag:
            queuedata: QueueData = self.passwords_queue.get()
            signal: Signal = queuedata.signal
            
            if signal is Signal.NoPasswordsLeft or signal is Signal.Success:
                if self.verbose:
                    cprint(f"[*] Recieved NoPasswordsLeft or Success", "magenta")
                self.passwords_queue.put(queuedata)
                break  
            
            password = queuedata.content
            
            login: Login = self.create_login(password)
            login.start()
    
    def threaded_bruteforce(self) -> None:  
        
        try:
            with ThreadPoolExecutor(max_workers=self.thread_n) as executor:
                while not self.stop_flag:
                    queuedata: QueueData = self.passwords_queue.get()
                    signal: Signal = queuedata.signal
                    # cprint(f"[PASSWORDS_QUEUE_LEN]: {self.passwords_queue.qsize()}", "green")
                    if signal is Signal.NoPasswordsLeft or signal is Signal.Success:
                        if self.verbose:
                            cprint(f"[*] Recieved NoPasswordsLeft or Success", "magenta")
                        self.passwords_queue.put(queuedata)
                        break  
                    password = queuedata.content
                    
                    self.semaphore.acquire()
                    with self.thread_lock:
                        self.running_n += 1              
                    # cprint(f"Creating new thread, semaphore = {self.running_n}")
                    if self.stop_flag:
                        break
                    
                    login: Login = self.create_login(password)
                    future: Future[None] = executor.submit(self.run_login, login)
                    self.futures.append(future)
                    sleep(0.1)
                    
        except KeyboardInterrupt:
            cprint(f"[!] Killing all bruteforcers", "red", attrs=["bold"])
        finally:
            if self.verbose:
                cprint(f"[TERMINATING]  BruteForcer", "cyan")
            self.wait_for_threads()
            return

    def create_login(self, password: str) -> Login:
        return self.login(
            target=self.target,
            password=password,
            results_queue=self.results_queue,
        )        
                    
    def run_login(self, login: Login) -> None:
        """Wrapper function to run login and release semaphore."""
        try:
            if not self.stop_flag:
                login.start()  # Run the login attempt
                # cprint(f"[+] Thread finished! {self.running_n} still running", "cyan")
        finally:
            with self.thread_lock:
                # Remove the future of this function from futures list if it exists
                self.running_n -= 1
                for future in list(self.futures):
                    if future.done():
                        self.futures.remove(future)
            self.semaphore.release()  # Ensure the semaphore is released after running

        
    def stop(self) -> None:
        self.stop_flag = True
        self.wait_for_threads()
        
    def wait_for_threads(self) -> None:
        if self.verbose:
            cprint(f"[*] Running threads {self.running_n}", "green")
        if self.verbose:
            cprint(f"[*] Waiting for {len(self.futures)} threads to finished", "green")
        
        for future in list(self.futures):
            try:
                future.result(timeout=0.1)  # This will block until the future is done
            except Exception as e:
                pass
        if self.verbose:
            cprint(f"[*] Done Waiting", "blue")
        
    def __len__(self) -> int:
        return self.thread_n
    
    def __repr__(self) -> str:
        return repr(self)
    
    def __str__(self) -> str:
        return f"{str(self.protocol).upper()}BruteForcer"


__all__ = ['BruteForcer']