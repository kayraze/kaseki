import queue
import multiprocessing as mp
from typing import Union, Callable, Optional, Any
import time
from termcolor import cprint

from . import producer
from . import queuecontent
from .queuecontent import QueueData, Signal

class QueueConsumer:
    """
    A class for consuming a queue and executing specified callbacks on each item.
    The consumer monitors for two signals: a `forward` signal and a `stop` signal.
    If a `forward` signal is received, data is forwarded to another queue.
    If a `stop` signal is received, the consumer halts processing.

    Attributes:
        data_queue (Union[queue.Queue, mp.Queue]): Queue containing data to be processed.
        forward_queue (Optional[Union[queue.Queue, mp.Queue]]): Queue to forward data upon receiving a `forward` signal.
        stop_signal (Optional[queuecontent.Signal]): Signal to stop consuming data.
        forward_signal (Optional[queuecontent.Signal]): Signal to forward data to `forward_queue`.
        data_callback (Optional[Callable]): Callback function for processing queue data.
        forward_callback (Optional[Callable]): Callback function for forwarded data.
        consume_delay (Union[int, float]): Delay (in seconds) between data consumption.
        stop_flag (bool): Flag indicating whether to stop consuming data.
    """
    
    def __init__(
            self,
            data_queue: Union[queue.Queue[QueueData], mp.Queue[QueueData]],
            forward_queue: Optional[Union[queue.Queue[QueueData], mp.Queue[QueueData]]] = None,
            stop_signal: Optional[Signal] = None,
            forward_signal: Optional[Signal] = None,
            data_callback: Optional[Callable[[QueueData], Signal]] = None,
            forward_callback: Optional[Callable[[QueueData], Signal]] = None,
            consume_delay: Union[int, float] = 0
        ):
        self.data_queue = data_queue
        self.forward_queue = forward_queue
        self.stop_signal = stop_signal
        self.forward_signal = forward_signal
        self.data_callback = data_callback
        self.forward_callback = forward_callback
        self.consume_delay = consume_delay
        self.stop_flag = False

    def consume(self) -> None:
        """
        Consumes data in a loop until a stop signal is received.
        """
        while not self.stop_flag:
            time.sleep(self.consume_delay)
            data: QueueData = self.get()
            if data.signal is Signal.Stop:
                self.clear_data_queue()
                self.stop()
            elif data.signal is Signal.Forward:
                self.forward(data)
            elif data.signal is Signal.Data:
                self.data_callback(data) if self.data_callback else None

    def get(
            self, 
            block: bool = True, 
            timeout: Optional[Union[int, float]] = None
        ) -> QueueData:
        """
        Retrieves data from the `data_queue`.

        Args:
            block (bool): Whether to block while waiting for data. Defaults to True.
            timeout (Optional[Union[int, float]]): Maximum wait time in seconds.

        Returns:
            queuecontent.QueueData: The retrieved data from the queue.
        """
        return self.data_queue.get(block=block, timeout=timeout)

    def put(
            self,
            data: Any, 
            block: bool = True, 
            timeout: Optional[Union[int, float]] = None
        ) -> None:
        """
        Puts data back into `data_queue`.

        Args:
            data (Any): The data to put in the queue.
            block (bool): Whether to block if the queue is full. Defaults to True.
            timeout (Optional[Union[int, float]]): Maximum wait time in seconds.
        """
        self.data_queue.put(data, block=block, timeout=timeout)

    def forward(
            self, 
            data: QueueData,
            block: bool = True,
            timeout: Optional[Union[int, float]] = None    
        ) -> None:
        """
        Forwards data to `forward_queue` if set.

        Args:
            data (queuecontent.QueueData): Data to forward.
            block (bool): Whether to block if the queue is full. Defaults to True.
            timeout (Optional[Union[int, float]]): Maximum wait time in seconds.
        """
        if self.forward_queue:
            self.forward_queue.put(data, block=block, timeout=timeout)

    def clear_data_queue(self) -> None:
        """
        Empties the data queue by retrieving all items.
        """
        try:
            while not self.data_queue.empty():
                self.get(block=False)
        except queue.Empty:
            pass

    def stop(self) -> None:
        """
        Sets the stop flag to terminate data consumption.
        """
        self.stop_flag = True


class PasswordConsumer:
    """
    A specialized consumer for handling passwords in a queue.

    Attributes:
        results_queue (Union[queue.Queue, mp.Queue]): Queue for processed password data.
        retry_queue (Optional[Union[queue.Queue, mp.Queue]]): Queue to hold data for retries.
        success_callback (Optional[Callable]): Callback function for successful passwords.
        retry_callback (Optional[Callable]): Callback for passwords needing retries.
        forward_callback (Optional[Callable]): Callback for forwarded passwords.
        failed_callback (Optional[Callable]): Callback for failed passwords.
        consume_delay (Union[int, float]): Delay (in seconds) between data consumption.
        verbose (bool): Flag for verbose output.
    """

    def __init__(
        self,
        results_queue: Union[queue.Queue[QueueData], mp.Queue[QueueData]],
        forward_queue: Optional[Union[queue.Queue[QueueData], mp.Queue[QueueData]]] = None,
        retry_queue: Optional[Union[queue.Queue[QueueData], mp.Queue[QueueData]]] = None,
        failed_callback: Optional[Callable[[QueueData], Signal]] = None,
        retry_callback: Optional[Callable[[QueueData], Signal]] = None,
        forward_callback: Optional[Callable[[QueueData], Signal]] = None,
        success_callback: Optional[Callable[[QueueData], Signal]] = None,
        consume_delay: Union[int, float] = 0,
        verbose: bool = True
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

    def consume(self) -> None:
        """
        Processes items in `results_queue` in an infinite loop.
        Each item is evaluated based on its signal and sent to the appropriate callback or queue.
        """
        while not self.stop_flag: 
            queuedata: queuecontent.QueueData = self.results_queue.get()
            # cprint(f"[CONSUMER]: queuedata with signal {queuedata.signal}", "yellow")
            if queuedata.signal is queuecontent.Signal.StopConsumer:
                self.stop()

            elif queuedata.signal is queuecontent.Signal.Success:
                if self.success_callback:
                    self.callback_evaluate(queuedata, self.success_callback)

            elif queuedata.signal is queuecontent.Signal.Failed:
                if self.failed_callback:
                    self.callback_evaluate(queuedata, self.failed_callback)

            elif queuedata.signal is queuecontent.Signal.Retry:
                self.retry_queue.put(queuedata) if self.retry_queue else None
                if self.retry_callback:
                    self.retry_callback(queuedata)

            elif queuedata.signal is queuecontent.Signal.Forward:
                self.forward_queue.put(queuedata) if self.forward_queue else None
                if self.forward_callback:
                    self.callback_evaluate(queuedata, self.forward_callback)

            time.sleep(self.consume_delay)

        if self.verbose:
            cprint("[+] PasswordConsumer successfully terminated", "yellow", attrs=["bold"])

        exit()

    def callback_evaluate(self, queuedata: QueueData, callback: Callable[[QueueData], Signal]) -> None:
        """
        Evaluates callback with `queuedata`, stops consumer if signal is `Finished`.

        Args:
            queuedata (queuecontent.QueueData): Data from the queue.
            callback (Callable): Callback function to process `queuedata`.
        """
        if callback(queuedata) is queuecontent.Signal.Finished:
            self.terminate()

    def terminate(self) -> None:
        """
        Drains the queue and stops the consumer.
        """
        self.drain_queue()
        self.stop()

    def drain_queue(self) -> None:
        """
        Empties `results_queue` to stop processing.
        """
        try:
            while not self.stop_flag:
                self.results_queue.get()
        except queue.Empty:
            if self.verbose:
                cprint("[!] Queue is empty.", "red")

    def clear_results_queue(self) -> None:
        """
        Clears all items from `results_queue`.
        """
        try:
            while not self.results_queue.empty():
                self.results_queue.get_nowait()
        except queue.Empty:
            pass
        if self.verbose:
            cprint("[*] Results queue is now empty", "yellow")

    def stop(self) -> None:
        """
        Sets stop flag to terminate consumer loop.
        """
        self.stop_flag = True

    def retry(self, queuedata: queuecontent.QueueData) -> None:
        """
        Sends data to `retry_queue` if set.

        Args:
            queuedata (queuecontent.QueueData): The data to be retried.
        """
        if self.retry_queue:
            self.retry_queue.put(queuedata)


__all__ = ['PasswordConsumer']