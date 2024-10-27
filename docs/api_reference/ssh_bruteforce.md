# SSH Brute Force Module

## Overview

`sshbruteforce.py` provides functionality for performing brute-force attacks on SSH servers. Users can specify various parameters for conducting these attacks efficiently, including target details, password sources, and threading options.

### Classes

This module contains the following classes to facilitate and automate SSH brute-forcing

### SSHBruteForcer

This class manages the brute-force attack process, supporting both single-threaded and multi-threaded execution.

#### Constructor

```python
def __init__(
    self,
    target: SSHTarget,
    passwords_queue: Union[queue.Queue, multiprocessing.Queue],
    results_queue: Union[queue.Queue, multiprocessing.Queue],
    login_thread_n: int = 0,
    max_login_retries: int = 100
):
    """Initialize the SSHBruteForcer with target server details and configuration.

    Args:
        target (SSHTarget): Details of the SSH target.
        passwords_queue (Queue): Queue containing passwords to attempt.
        results_queue (Queue): Queue for storing the results of login attempts.
        login_thread_n (int): Number of threads for concurrent login attempts.
        max_login_retries (int): Maximum number of login retries per password.
    """

```

#### Example

Here is a basic example to utilize the SSHBruteForcer, you must specify the `target` (of type SSHTarget), the `passwords_queue` from which all threads will draw passwords, and the `results_queue` where each thread will store the outcome of its login attempts. You can also set the number of threads for concurrent attempts via `login_thread_n`

```python
passwords_queue = queue.Queue()  # Queue for passwords to be tried
results_queue = queue.Queue()    # Queue for storing login results
bruteforcer = SSHBruteForcer(
    target=SSHTarget(
        hostname='192.168.18.1',
        port=22,
        username='root'
    ),
    passwords_queue=passwords_queue,
    results_queue=results_queue,
    login_thread_n=10,
)

bruteforcer.run()                # Run in standalone mode
bruteforcer.threaded_run()       # Run with threading (non-blocking)
bruteforcer.multiprocessed_run() # Run in a separate process (non-blocking)
```

### SSHTarget

This class encapsulates the SSH target details, including hostname, port, and username. While it is not strictly necessary, using `SSHTarget` helps maintain clean and organized code, especially since target information is frequently passed as arguments to various functions and methods.

#### Constructor

```python
def __init__(self, hostname: str = "localhost", port: int = DEFAULT_PORT, username: Optional[str] = None, verbose: bool = False):
    """Initialize the SSHTarget with hostname, port, and optional username.

    Args:
        hostname (str): SSH server hostname or IP address.
        port (int): Port number for the SSH service.
        username (Optional[str]): Username for SSH login, if specified.
        verbose (bool): Flag to enable or disable verbose logging.
    """
```

### SSHLoginThreadInfo

This class stores information about the currently running SSH login threads, specifically when using multi-threading. It captures the thread ID and the associated thread object, allowing the SSHBruteForcer to manage the threads effectively.

#### Constructor

```python
class SSHLoginThreadInfo:
    """A class representing a thread's identity and associated information.

    Attributes:
        thread_id (int): A unique identifier for the thread.
        thread_obj (threading.Thread): The associated thread object.
    """

    def __init__(self, thread_id: int, thread_obj: threading.Thread):
        """Initialize SSHLoginThreadInfo with a thread ID and object.

        Args:
            thread_id (int): A unique identifier for the thread.
            thread_obj (threading.Thread): The actual thread object.
        """
        self.thread_id: int = thread_id
        self.thread_obj: threading.Thread = thread_obj

```
