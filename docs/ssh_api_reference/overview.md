# Overview

## SSH Brute Forcer

`sshbruteforcer.py` is designed to perform brute-force attacks on SSH servers. It provides the necessary tools for users to automate the process of attempting various password combinations to gain unauthorized access to the target system. The module supports both single-threaded and multi-threaded execution, allowing for flexibility in performance based on user needs.

## Key Features

- Automates the SSH brute-force attack process.
- Supports configuration for target server details and password lists.
- Allows for multi-threaded execution to enhance attack speed and efficiency.

## SSH Brute Force Manager

`sshbruteforcemanager.py` acts as a centralized manager for conducting SSH brute-force attacks. It orchestrates the coordination between password generation and the consumption of results from the brute-force attempts. This module enhances overall efficiency by utilizing multiprocessing, allowing for simultaneous processing of password attempts and results collection.

## Key Features

- Manages password production and result consumption for brute-force attacks.
- Utilizes multiprocessing to improve performance and responsiveness.
- Provides an easy-to-use interface for configuring and executing brute-force operations.
