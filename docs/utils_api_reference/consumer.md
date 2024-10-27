# Consumer Module Overview

## Overview

`consumer.py` implements the `QueueConsumer` and `PasswordConsumer` classes, designed for efficiently consuming data from queues in a multi-processing environment. This module facilitates the processing of items, enabling actions based on various signals received from the queue. It is essential for managing the flow of data in applications that require handling multiple tasks concurrently.

---

## QueueConsumer

`QueueConsumer` is responsible for monitoring a queue for incoming data and executing specified callbacks on each item. It operates by listening for different signals that dictate how to handle the data, such as forwarding it to another queue or stopping consumption altogether.

## Key Features

- Monitors a data queue and processes items based on defined signals.
- Supports optional forwarding of data to another queue.
- Utilizes callbacks to handle data processing dynamically.
- Includes configurable delays between data consumption to manage processing rates.

---

## PasswordConsumer

`PasswordConsumer` is a specialized version of the `QueueConsumer` focused on handling password data. It processes results from password attempts, invoking appropriate callbacks for success, failure, and retries. This consumer is crucial for applications that involve brute-force password attacks, as it effectively manages the outcomes of each attempt.

## Key Features

- Processes password data from a results queue with specific handling for success and failure.
- Supports retrying of passwords and forwarding data to another queue if necessary.
- Implements configurable verbosity for logging the status of operations.
- Provides mechanisms to clean up and drain queues when stopping the consumer.

---
