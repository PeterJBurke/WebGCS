# WebGCS Raspberry Pi Setup Guide

This document provides instructions on how to set up the WebGCS application on a Raspberry Pi using the provided `setup_raspberry_pi.sh` script. This script automates the installation of dependencies, cloning of the repository, and configuration of a systemd service to run the application on boot.

## Prerequisites

*   A Raspberry Pi (any model should work, but Pi 3 or newer is recommended) with a fresh installation of Raspberry Pi OS (formerly Raspbian). Lite version is sufficient.
*   Internet connectivity on the Raspberry Pi.
*   Access to the Raspberry Pi via SSH or a direct terminal.

## Setup Instructions

1.  **Log in to your Raspberry Pi.**

2.  **Download the setup script:**
    You can download the script directly from the GitHub repository using `curl` or `wget`. If `git` is already installed (it might not be on a bare minimum image), you could clone the repo first, but the script itself installs git.

    ```bash
    curl -O https://raw.githubusercontent.com/PeterJBurke/WebGCS/main/setup_raspberry_pi.sh
    ```
    Alternatively, if you have `wget`:
    ```bash
    wget https://raw.githubusercontent.com/PeterJBurke/WebGCS/main/setup_raspberry_pi.sh
    ```

3.  **Make the script executable:**
    ```bash
    chmod +x setup_raspberry_pi.sh
    ```

4.  **Run the script with sudo privileges:**
    The script needs sudo to install packages and set up the systemd service.
    ```bash
    sudo ./setup_raspberry_pi.sh
    ```
    The script will perform the following steps:
    *   Update and upgrade system packages.
    *   Install `git`, `python3`, `python3-pip`, and `python3-venv`.
