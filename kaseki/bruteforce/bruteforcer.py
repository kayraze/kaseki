from termcolor import cprint
from typing import Union, Callable, List, Type
import queue as q
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, Future
import threading as td

from .utils import  get_protocol_type_with_target, get_login_type_with_target
from kaseki.bruteforce.login import Login
from .target import Target
from kaseki.bruteforce.protocol import Protocol
from kaseki.utils import QueueData, Signal

class BruteForcer:
    
    def __init__(
        self, 
        target: Target,
        passwords_queue: Union[q.Queue[QueueData], mp.Queue[QueueData]], 
        results_queue: Union[q.Queue[QueueData], mp.Queue[QueueData]],
        thread_n: int=0, 
        max_attempts:int=10,
    ):
        self.target = target
        self.passwords_queue = passwords_queue
        self.results_queue = results_queue
        self.thread_n = thread_n
        self.max_attempts = max_attempts
        
        self.stop_flag: bool = False
        self.futures: List[Future[None]] = []
        self.semaphore: td.Semaphore = td.Semaphore(thread_n)
        self.running_n: int = 0
        self.thread_lock: td.Lock = td.Lock()
        
        self.protocol: Type[Protocol] = get_protocol_type_with_target(target)
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
                    
        except Exception as e:
            cprint(f"[ERROR]    BruteForcer: {e}", "red", attrs=["bold"])
        finally:
            cprint(f"[TERMINATING]  BruteForcer", "cyan")
            self.wait_for_threads()
            return

    def create_login(self, password) -> Login:
        return self.login(
            target=self.target,
            password=password,
            results_queue=self.results_queue,
            max_attempts=20
        )        
                    
    def run_login(self, login) -> None:
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
        cprint(f"[*] Running threads {self.running_n}", "green")
        cprint(f"[*] Waiting for {len(self.futures)} threads to finished", "green")
        
        for future in list(self.futures):
            try:
                future.result(timeout=3)  # This will block until the future is done
            except Exception as e:
                print(f"Error while waiting for future: {e}")
        cprint(f"[*] Done Waiting", "blue")


__all__ = ['BruteForcer']