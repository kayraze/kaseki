import queue
import queuecontent
import multiprocessing
from typing import Union, Callable, Optional, Any
import time
import producer
from termcolor import cprint

class QueueConsumer:

    """
    A class for consuming a queue and calling a callback for it
    it also listens for two different values, a forward value and
    a stop value, when a forward value is recieved it pushes it 
    to the queue, if a stop value is recieved it immediately stops
    recieving value

    Attributes:
        data_queue (queue.Queue): Contains the data to be consumed
        forward_queue: (queue.Queue): Data recieved from data_queue is forwarded here
        
    """

    def __init__(
            self,
            data_queue: Union[queue.Queue, multiprocessing.Queue],
            forward_queue: Optional[Union[queue.Queue, multiprocessing.Queue]]=None,
            stop_signal: Optional[queuecontent.Signal]=None,
            forward_signal: Optional[queuecontent.Signal]=None,
            data_callback: Optional[Callable] = None,
            forward_callback: Optional[Callable] = None,
            consume_delay: Union[int, float]=0
        ):
        self.data_queue:  Union[queue.Queue, multiprocessing.Queue] = data_queue   
        self.forward_queue:  Optional[Union[queue.Queue, multiprocessing.Queue]] = forward_queue
        self.stop_signal: Optional[queuecontent.Signal] = stop_signal
        self.forward_signal: Optional[queuecontent.Signal] = forward_signal
        self.data_callback: Optional[Callable] = data_callback
        self.forward_callback: Optional[Callable] = forward_callback
        self.consume_delay: Union[int, float] = consume_delay
        self.stop_flag: bool = False

    def consume(self) -> None:
        """
        Consumes data in a loop until a stop signal is recieved
        """
        while not self.stop_flag:
            time.sleep(self.consume_delay)
            data: queuecontent.QueueData = self.get()
            if data.signal is queuecontent.Signal.Stop:
                self.clear_data_queue()
                self.stop()
            elif data.signal is queuecontent.Signal.Forward:
                self.forward(data)
            elif data.signal is queuecontent.Signal.Data:
                self.data_callback(data) if self.data_callback else None

    def get(
            self, 
            block:bool=True, 
            timeout:Optional[Union[int, float]]=None
        ) -> queuecontent.QueueData:
        return self.data_queue.get(
            block=block,
            timeout=timeout,
        )

    def put(
            self,
            data:Any, 
            block:bool=True, 
            timeout:Optional[Union[int, float]]=None
        ) -> None:
        return self.data_queue.put(
            data,
            block=block,
            timeout=timeout,
        )
    def forward(
            self, 
            data: queuecontent.QueueData,
            block: bool=True,
            timeout: Optional[Union[int, float]]=None    
        ) -> None:
        if self.forward_queue:
            self.forward_queue.put(
                data,
                block=block,
                timeout=timeout
            )

    def clear_data_queue(self):
        try:
            while not self.data_queue.empty():
                self.get(block=False)
        except (queue.Empty):
            pass

    def stop(self):
        self.stop_flag = True

class PasswordConsumer:
    """
    Password Consumer
    """
    def __init__(
        self,
        results_queue: Union[queue.Queue, multiprocessing.Queue],
        forward_queue: Optional[Union[queue.Queue, multiprocessing.Queue]]=None,
        retry_queue:  Optional[Union[queue.Queue, multiprocessing.Queue]]=None,
        failed_callback: Optional[Callable] = None,
        retry_callback: Optional[Callable] = None,
        forward_callback: Optional[Callable] = None,
        success_callback: Optional[Callable] = None,
        consume_delay: Union[int, float]=0,
        verbose: bool=False
    ):

        self.results_queue = results_queue
        self.retry_queue = retry_queue
        self.success_callback = success_callback
        self.retry_callback = retry_callback
        self.forward_queue = forward_queue
        self.failed_callback = failed_callback
        self.forward_callback = forward_callback
        self.consume_delay = consume_delay
        self.stop_flag = False
        self.verbose = verbose

    # Consume data in the
    def consume(self):
        """
        Starts an infinite loop and gets a queuedata
        from the results_queue then processes it
        by evaluating the signal it contains.
        """
        while not self.stop_flag: 
            queuedata: queuecontent.QueueData = self.results_queue.get()

            # A signal for stopping the consumer
            if queuedata.signal is queuecontent.Signal.StopConsumer:
                self.stop()

            # A signal for a success usually meaning password found
            elif queuedata.signal is queuecontent.Signal.Success:
                if self.success_callback:
                    self.callback_evaluate(queuedata, self.success_callback)

            # A Signal for password failed
            elif queuedata.signal is queuecontent.Signal.Failed:
                if self.failed_callback:
                    self.callback_evaluate(queuedata, self.failed_callback)

            # A Signal for password retry, password is placed back
            # to the passwords queue for another attempt aka retry
            elif queuedata.signal is queuecontent.Signal.Retry:
                self.retry_queue.put(queuedata) if self.retry_queue else None
                if self.retry_callback:
                    self.retry_callback(queuedata)

            # A Signal to forward the queuedata to another queue or
            # pass to the forward_callback
            elif queuedata.signal is queuecontent.Signal.Forward:
                if self.forward_queue:
                    self.forward_queue.put(queuedata)
                if self.forward_callback:
                    self.callback_evaluate(queuedata, self.forward_callback)
            
            # Consume delay
            time.sleep(self.consume_delay)

        if self.verbose:
            cprint("[+] PasswordConsumer successfuly terminated", "yellow", attrs=["bold"])
        
        exit()

    def callback_evaluate(self, queuedata, callback):
        if callback(queuedata) is queuecontent.Signal.Finished:
            self.terminate()

    def terminate(self):
        self.clear_results_queue()
        self.drain_queue()
        self.clear_results_queue()
        self.stop()

    def drain_queue(self):
        try:
            while not self.stop_flag:
                self.results_queue.get()
        except queue.Empty:
                cprint("[!] Empty exception", "red") if self.verbose else None
                pass
        cprint("[*] results queue is now wasted, terminating..","yellow") if self.verbose else None

    def clear_results_queue(self):
        try:
            while not self.results_queue.empty():
                self.results_queue.get_nowait()
        except queue.Empty:
            pass
        cprint("[*] results queue is now empty","yellow") if self.verbose else None


    def stop(self) -> None:
        self.stop_flag = True


    def retry(self, queuedata: queuecontent.QueueData) -> None:
        self.retry_queue.put(queuedata) if self.retry_queue else None


def success(queuedata: queuecontent.QueueData) -> queuecontent.Signal:
    cprint(f"{str(queuedata.signal)} -> {queuedata.content}", "green")
    return queuecontent.Signal.Finished


def failed(queuedata: queuecontent.QueueData) -> queuecontent.Signal:
    cprint(f"{str(queuedata.signal)} -> {queuedata.content}", "red")
    return queuecontent.Signal.Ignore

if __name__ == '__main__':
    passwords_queue: multiprocessing.Queue = multiprocessing.Queue()
    results_queue: multiprocessing.Queue = multiprocessing.Queue()
    
    password_producer = producer.PasswordProducer(
        "100-worst-passwords.txt",
        passwords_queue
    )
    password_producer.produce()
    
    password_consumer = PasswordConsumer(
        results_queue=results_queue,
        retry_queue=passwords_queue,
        success_callback=success,
        failed_callback=failed
    )

    for _ in range(50):
        results_queue.put(queuecontent.QueueData(
            queuecontent.Signal.Failed,
            passwords_queue.get()
        ))
    results_queue.put(queuecontent.QueueData(
        queuecontent.Signal.Success,
        "Please stop the consumer"
    ))
    for _ in range(40):
        results_queue.put(queuecontent.QueueData(
            queuecontent.Signal.Failed,
            passwords_queue.get()
        ))
    password_consumer.consume()
    cprint(f"[PASSWORD_QUEUE_LEN]: {passwords_queue.qsize()}")
    cprint(f"[RESULT_QUEUE_LEN]: {results_queue.qsize()}")
