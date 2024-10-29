import argparse
import sys
from termcolor import cprint
from typing import Type, Optional

from .bruteforce.target import Target, SSHTarget, FTPTarget 
from .bruteforce.protocol import Protocol, SSH, FTP

from .bruteforce import BruteForceManager

def get_target_type_with_str(protocol_str: str) -> Optional[Type[Target]]:
    cprint(f"{protocol_str.lower()} == ssh: {protocol_str.lower() == 'ssh'}", "cyan")
    if protocol_str.lower() == "ssh":
        return SSHTarget
    elif protocol_str.lower() == "ftp":
        return FTPTarget
    return None

# def get_default_port_with_protocol(protocol: Type[Protocol]) -> Optional[int]:
#     if issubclass(protocol, SSH):
#         return 22
#     elif issubclass(protocol, FTP):
#         return 21
#     return None

SUPPORTED_PROTOCOL_STRING_ARGS=["ssh", "ftp"]

def main() -> None:

    # This error file will redirect error stream/output to the file if debug not set
    # This was made due to paramiko ssh connect making uncatchable EOF & Banner Error exceptions
    error_file = open('/dev/null', 'w')

    # Get command line arguments
    parser = argparse.ArgumentParser(description="SSH Brute Force Tester")
    parser.add_argument("protocol", choices=SUPPORTED_PROTOCOL_STRING_ARGS, help="Target SSH protocol")
    parser.add_argument("hostname", default="localhost", help="Hostname or IP of the SSH server")
    
    parser.add_argument("--username", "-u", required=True, help="Username for SSH login")
    parser.add_argument("--passlist", "-P", required=True, help="File containing list of passwords")
    
    parser.add_argument("--threads", "-t", type=int, default=10, help="Amount of threads per process")
    parser.add_argument("--processes", "--procs", type=int, default=0, help="Amount of processes")
    
    parser.add_argument("--port", "-p", type=int, help="SSH port (default is 22)")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable error outputs")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Relay the stderr stream to error_file if not in debug mode (default)
    sys.stderr = sys.stderr if args.debug else error_file

    # Amount of multiprocessed bruteforce to run
    process_n = args.processes or 0

    # Amount of thread per bruteforcer regardless if multiprocessed or not
    thread_n: int = int(args.threads) or 0

    # Path to the password file containing one password per line
    passlist: str = args.passlist

    # If verbose
    verbose: bool = args.verbose
    
    # The target protocol 
    protocol_str: str = args.protocol

    target_type: Optional[Type[Target]] = get_target_type_with_str(protocol_str)

    # protocol: Type[Protocol] = get_protocol_type_with_target(target_type())

    hostname: str = args.hostname
    port: Optional[int] = int(args.port) if args.port else None
    username: str = args.username
    cprint(f"port = {port}", "cyan")
    if not target_type or not issubclass(target_type, Target) or not port:
        cprint(f"[!] Invalid protocol: {protocol_str}", "red", attrs=["bold"])
        cprint(f"[!] Select supported protocols in {SUPPORTED_PROTOCOL_STRING_ARGS}")
        return
    
    cprint(f"[*] Starting {protocol_str.upper()} Bruteforce Session", "blue", attrs=["bold"])
    cprint(f"[*] Target: {username}@{hostname}{f':{port}' if port else ''}", "blue")
    cprint(f"[*] Processes: {process_n}", "blue") if process_n else None
    cprint(f"[*] {'Threads each process' if process_n > 0 else 'Threads'}: {thread_n}", "blue")
    cprint(f"[*] Total threads: {thread_n * process_n if process_n > 0 else thread_n}", "blue") if process_n > 0 else None
    print("")


    # Create SSH target object
    target = target_type(
        hostname=hostname, 
        username=username,
        port=port
    )

    # This will manage our bruteforcers, password producer, and result consumer
    brute_forcer = BruteForceManager(
        target, 
        passlist,
        verbose=verbose
    )

    # Initialize/starts our producers and consumers and then the bruteforcers
    brute_forcer.start(
        process_n=process_n,
        login_thread_n_each=thread_n,
    )
    cprint("[*] Finished", "blue", attrs=["bold"]) if verbose else None

if __name__ == "__main__":
    main()


__all__: list[str] = ['get_target_type_with_str']