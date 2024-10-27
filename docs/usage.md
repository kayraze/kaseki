# Usage Guide for the Password Processing System

## Introduction

- This guide provides instructions on how to utilize the password processing system, which includes producing passwords from a file and consuming them for processing. It covers setup, configuration, and usage of the core components: `PasswordProducer`, `PasswordConsumer`, and the message passing structure defined in `queuecontent.py`.

---

## Requirements

Python 3.x
Required libraries:

- `termcolor`
- `queue`
- `multiprocessing`

---

## Setup

1. **Install Dependencies**: Ensure all necessary libraries are installed. You can use pip to install termcolor if it's not already available.

```bash
pip install termcolor
```

2. **File Structure**: Organize your project files as follows:

- ```

  ```

- /your_project_directory/
-        ├── producer.py
-        ├── consumer.py
-        ├── queuecontent.py
-        ├── main.py
-        └── passwords.txt  # Your password file
- ```

  ```

3. **Prepare Password File**: Create a text file (e.g., `passwords.txt`) containing one password per line.

---

## Example Usage

### Main Script (`main.py`)

The main script will orchestrate the producer and consumer processes. Here is a sample implementation:

```python
import queue
import multiprocessing
from producer import PasswordProducer
from consumer import PasswordConsumer
from queuecontent import QueueData, Signal

def main():
    # Initialize queues
    passwords_queue = multiprocessing.Queue()
    results_queue = multiprocessing.Queue()

    # Create producer
    password_filename = "passwords.txt"  # Specify your password file here
    producer = PasswordProducer(password_filename, passwords_queue, termination_value=None, delay=0.1, verbose=True)

    # Create consumer
    consumer = PasswordConsumer(results_queue, passwords_queue, consume_delay=0.1, verbose=True)

    # Start producer and consumer processes
    producer_process = multiprocessing.Process(target=producer.produce)
    consumer_process = multiprocessing.Process(target=consumer.consume)

    producer_process.start()
    consumer_process.start()

    # Wait for processes to finish
    producer_process.join()
    consumer_process.join()

if __name__ == "__main__":
    main()
```
