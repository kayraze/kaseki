import argparse
import sys
from termcolor import cprint  # For color output
from kaseki.sshbruteforce import SSHTarget
from kaseki.kaseki import SSHBruteForceManager

error_file = open('/dev/null', 'w')

def main():
    parser = argparse.ArgumentParser(description="SSH Brute Force Tester")
    parser.add_argument("hostname", default="localhost", help="Hostname or IP of the SSH server")
    parser.add_argument("--username", "-u", help="Username for SSH login")
    parser.add_argument("--passlist", "-P", help="File containing list of passwords")
    parser.add_argument("--threads", "-t", type=int, default=10, help="Amount of threads per process")
    parser.add_argument("--processes", "--procs", type=int, default=0, help="Amount of processes")
    parser.add_argument("--port", "-p", type=int, default=22, help="SSH port (default is 22)")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable error outputs")

    args = parser.parse_args()
    sys.stderr = sys.stderr if args.debug else error_file

    process_n = args.processes or 0
    thread_n = args.threads or 0
    hostname = args.hostname
    port = args.port
    username = args.username
    passlist = args.passlist

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
        process_n=process_n,
        login_thread_n_each=thread_n,
    )
    cprint("[*] Finished", "blue", attrs=["bold"])

if __name__ == "__main__":
    main()
