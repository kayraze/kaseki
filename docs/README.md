# Kaseki

Kaseki is an SSH Brute Force Testing tool designed to help security professionals assess the security of SSH servers. It allows you to test multiple usernames and password combinations in a configurable and "multiprocessed-threaded" manner.

## Features

Brute force login attempts against SSH servers.
Support for multiple threads and processes to optimize performance.
Customizable parameters for hostname, username, password list, and more.
Colorful console output for better readability.

## Installation

You can install Kaseki using pip. Clone the repository and run the following command in the project root directory (where setup.py is located):

```bash
git clone https://github.com/kayraze/kaseki.git
cd kaseki
pip install .
```

### Usage

After installation, you can run Kaseki from the command line:

kaseki <hostname> [options]

### Arguments

<hostname>: The hostname or IP address of the SSH server (default is localhost).
-u, --username: The username for SSH login (optional).
-P, --passlist: The file containing the list of passwords (optional).
-t, --threads: Number of threads to use (default is 10).
--proc: sNumber of processes to use (default is 0, which means no multiprocessing).
-p, --port: The SSH port (default is 22).
-d, --debug: Enable error outputs for debugging.
Example
-v, --verbose: Enable logging outputs

kaseki 192.168.1.100 -u admin -P passwords.txt -t 5 --procs 2

### Contributing

Contributions are welcome! Please feel free to submit issues, create pull requests, or provide suggestions for improvements.

#### License

This project is licensed under the MIT License. See the LICENSE file for details.

##### Acknowledgments

Paramiko for SSH connectivity.
Termcolor for colored terminal output.
