import ftplib
from kaseki.brutemanager.target import FTPTarget
from kaseki.utils.queuecontent import Signal, QueueData

import ftplib
from kaseki.brutemanager.target import FTPTarget
from kaseki.utils.queuecontent import Signal, QueueData

class FTPLogin:
    
    def __init__(self, hostname: str, username: str, password: str, results_queue, max_attempts: int = 0):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.results_queue = results_queue
        self.max_attempts = max_attempts
        self.stop_flag = False
        self.ftps = ftplib.FTP()  # Class-level instance of FTP

    def start(self):
        attempts: int = 0
        result: Signal = Signal.Blank

        while not self.stop_flag:
            try:
                # Connect to the FTP server
                self.ftps.connect(self.hostname)

                # Log in to the server
                self.ftps.login(user=self.username, passwd=self.password)
                result = Signal.Success
                break  # Exit the loop on successful login

            except ftplib.error_perm:
                result = Signal.Failed
                break  # Exit on permission error

            except ftplib.error_temp:
                attempts += 1
                if attempts >= self.max_attempts:
                    result = Signal.Retry
                    break  # Exit if maximum attempts reached

            except Exception as e:
                result = Signal.Error
                print(f"An unexpected error occurred: {e}")  # Optional logging
                break  # Exit on unexpected error
            
            finally:
                try:
                    self.ftps.quit()  # Ensure we quit the FTP connection
                except Exception as e:
                    print(f"Error quitting FTP: {e}")  # Optional logging

                # Queue the result after each attempt
                self.results_queue.put(
                    QueueData(
                        result,
                        self.password
                    )
                )
                    
    def stop(self):
        """Stop the login attempts."""
        self.stop_flag = True
