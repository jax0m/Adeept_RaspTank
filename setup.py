#!/usr/bin/python3
# File name   : setup.py
# Author      : Adeept
# Date        : 2020/3/14

import os
import sys
import subprocess
import logging
import datetime
from pathlib import Path

# Configure logging
log_directory = '/var/log/adeept_rasptank'
log_file = os.path.join(log_directory, f'setup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# Create log directory if it doesn't exist
os.makedirs(log_directory, exist_ok=True)

# Configure logging to write to file and console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(log_file),
    logging.StreamHandler(sys.stdout)
])

# Get the absolute path of the script
curpath = os.path.realpath(__file__)
thisPath = os.path.dirname(curpath)

# Function to run shell commands with error handling
def run_command(command, check=True):
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        logging.info(f"Command executed successfully: {command}")
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {command}\nError: {e.stderr}")
        return None

# Function to replace text in a file
def replace_text_in_file(file_path, old_text, new_text):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        if old_text in content:
            content = content.replace(old_text, new_text)
            with open(file_path, 'w') as file:
                file.write(content)
            logging.info(f"Replaced text in {file_path}")
        else:
            logging.warning(f"Text not found in {file_path}: {old_text}")
    except Exception as e:
        logging.error(f"Error replacing text in {file_path}: {str(e)}")

# Function to create startup script
def create_startup_script():
    startup_script_path = os.path.expanduser('~/startup.sh')
    try:
        with open(startup_script_path, 'w') as f:
            f.write("#!/bin/sh\n")
            f.write(f"sudo python3 {thisPath}/server/webServer.py\n")
        logging.info(f"Created startup script at {startup_script_path}")
        # Make the script executable
        subprocess.run(['sudo', 'chmod', '777', startup_script_path], check=True)
    except Exception as e:
        logging.error(f"Error creating startup script: {str(e)}")

# Function to update rc.local
def update_rc_local():
    rc_local_path = '/etc/rc.local'
    try:
        # Check if rc.local exists
        if not os.path.exists(rc_local_path):
            logging.warning(f"rc.local not found at {rc_local_path}. Skipping update.")
            return

        # Read the file
        with open(rc_local_path, 'r') as f:
            content = f.read()

        # Check if the startup script is already added
        if "//home/pi/startup.sh start" in content:
            logging.info("Startup script already added to rc.local")
            return

        # Add the startup script call
        new_content = content.replace("fi", "fi\n//home/pi/startup.sh start")
        with open(rc_local_path, 'w') as f:
            f.write(new_content)
        logging.info("Added startup script to rc.local")
    except Exception as e:
        logging.error(f"Error updating rc.local: {str(e)}")

# Function to enable I2C
def enable_i2c():
    # Check if the system has /boot/firmware/config.txt (common on newer Raspberry Pi OS)
    config_path = '/boot/firmware/config.txt'
    if not os.path.exists(config_path):
        # Fallback to /boot/config.txt for older systems
        config_path = '/boot/config.txt'
    
    try:
        # Check if config.txt exists
        if not os.path.exists(config_path):
            logging.warning(f"config.txt not found at {config_path}. Skipping I2C enablement.")
            return

        # Read the file
        with open(config_path, 'r') as f:
            content = f.read()

        # Check if I2C is already enabled
        if 'dtparam=i2c_arm=on' in content:
            logging.info("I2C is already enabled")
            return

        # Enable I2C
        new_content = content.replace('#dtparam=i2c_arm=on', 'dtparam=i2c_arm=on\nstart_x=1')
        with open(config_path, 'w') as f:
            f.write(new_content)
        logging.info(f"Enabled I2C in {config_path}")
    except Exception as e:
        logging.error(f"Error enabling I2C: {str(e)}")

# Function to blacklist sound module
def blacklist_sound_module():
    blacklist_path = '/etc/modprobe.d/snd-blacklist.conf'
    try:
        # Check if the file exists
        if os.path.exists(blacklist_path):
            logging.info(f"Sound module blacklist file already exists at {blacklist_path}")
            return

        # Create the file and write the blacklist entry
        with open(blacklist_path, 'w') as f:
            f.write("blacklist snd_bcm2835\n")
        logging.info(f"Created sound module blacklist at {blacklist_path}")
    except Exception as e:
        logging.error(f"Error creating sound module blacklist: {str(e)}")

# Function to install packages from requirements.txt
def install_requirements():
    requirements_path = os.path.join(thisPath, 'server', 'requirements.txt')
    try:
        # Check if requirements.txt exists
        if not os.path.exists(requirements_path):
            logging.warning(f"requirements.txt not found at {requirements_path}. Skipping package installation.")
            return

        # Install packages using pip in a temporary virtual environment
        logging.info("Installing packages from requirements.txt")
        
        # Create a temporary virtual environment
        venv_path = os.path.join(thisPath, '.venv')
        venv_cmd = f"python3 -m venv {venv_path}"
        result = run_command(venv_cmd)
        if result is None:
            logging.error("Failed to create virtual environment")
            return
        
        # Activate the virtual environment and upgrade pip
        logging.info("Activate the virtual environment and upgrading pip")
        install_cmd = f"source {venv_path}/bin/activate && pip3 install -U pip"
        result = run_command(install_cmd, check=False)
        # Activate the virtual environment and install packages
        install_cmd = f"source {venv_path}/bin/activate && pip install -r {requirements_path}"
        result = run_command(install_cmd, check=False)
        if result is None:
            logging.error("Failed to install packages from requirements.txt")
            return

        logging.info("Successfully installed packages from requirements.txt")
    except Exception as e:
        logging.error(f"Error installing requirements: {str(e)}")

# Function to install additional packages
def install_additional_packages():
    # Check if we're on a system that uses apt-get
    if not os.path.exists('/usr/bin/apt-get'):
        logging.warning("Cannot find apt-get. Skipping package installation.")
        return
    
    # Use a more robust approach to install packages
    packages = [
        'python3-dev',
        'python3-pip',
        'libfreetype6-dev',
        'libjpeg-dev',
        'build-essential',
        'i2c-tools',
        # 'libjasper-dev',
        # 'libatlas-base-dev',
        'libgstreamer1.0-0',
        'python3-opencv',
        'python3-smbus',
        'util-linux',
        'procps',
        'hostapd',
        'iproute2',
        'iw',
        'haveged',
        'dnsmasq',
        # 'libqtgui4',
        'libhdf5-dev',
        'libhdf5-serial-dev',
        # 'libqt4-test',
        'luma.oled',
        # 'adafruit-pca9685',
        # 'rpi-ws281x',
        # 'mpu6050-raspberrypi',
        # 'flask',
        # 'flask_cors',
        # 'websockets',
        # 'numpy',
        # 'imutils',
        # 'zmq',
        # 'pybase64',
        # 'psutil',
        'RPi.GPIO'
    ]

    try:
        logging.info("Installing additional packages")
        # Use a more reliable approach to install packages
        result = run_command(f"sudo apt-get install -y {' '.join(packages)}")
        if result is None:
            logging.error("Failed to install additional packages")
            return

        logging.info("Successfully installed additional packages")
    except Exception as e:
        logging.error(f"Error installing additional packages: {str(e)}")

# Function to clone and install create_ap
def install_create_ap():
    create_ap_dir = os.path.join(thisPath, 'create_ap')
    try:
        # Check if create_ap directory already exists
        if os.path.exists(create_ap_dir):
            logging.info("create_ap directory already exists")
            return

        # Clone create_ap repository
        logging.info("Cloning create_ap repository")
        result = run_command(f"git clone https://github.com/oblique/create_ap {create_ap_dir}")
        if result is None:
            logging.error("Failed to clone create_ap repository")
            return

        # Install create_ap
        logging.info("Installing create_ap")
        result = run_command(f"cd {create_ap_dir} && sudo make install")
        if result is None:
            logging.error("Failed to install create_ap")
            return

        logging.info("Successfully installed create_ap")
    except Exception as e:
        logging.error(f"Error installing create_ap: {str(e)}")

# Function to check if user has sudo privileges
def check_sudo_privileges():
    try:
        # Check if the user is root (uid 0)
        if os.geteuid() == 0:
            logging.info("User has sudo privileges")
            return True
        
        # Try to run a command that requires sudo to check if the user can execute it
        result = subprocess.run(['sudo', '-n', 'echo', 'test'], capture_output=True, text=True)
        if result.returncode == 0:
            logging.info("User has sudo privileges")
            return True
        else:
            logging.error("User does not have sudo privileges")
            return False
    except Exception as e:
        logging.error(f"Error checking sudo privileges: {str(e)}")
        return False

# Function to get user confirmation
def get_user_confirmation(prompt):
    while True:
        try:
            response = input(f"{prompt} (y/n): ").lower()
            if response in ['y', 'yes', 'ye', 'yeah', 'sure']:
                return True
            elif response in ['n', 'no', 'nah', 'nope']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return False

# Function to check if create_ap is installed
def is_create_ap_installed():
    try:
        result = subprocess.run(['which', 'create_ap'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

# Main function
def main():
    logging.info("Starting Raspberry Pi Robot setup")

    # Check if user has sudo privileges
    if not check_sudo_privileges():
        logging.error("This script requires sudo privileges to run. Please run with 'sudo python3 setup.py'")
        sys.exit(1)
    
    # Prompt for installation confirmation
    if not get_user_confirmation("Are you sure you want to proceed with the Raspberry Pi Robot installation?"): 
        logging.info("Installation cancelled by user")
        sys.exit(0)
    
    # Update package list
    logging.info("Updating package list")
    run_command("sudo apt-get update")

    # Clean up packages
    logging.info("Cleaning up packages")
    run_command("sudo apt-get purge -y wolfram-engine")
    run_command("sudo apt-get purge -y libreoffice*")
    run_command("sudo apt-get -y clean")
    run_command("sudo apt-get -y autoremove")

    # Install additional packages
    install_additional_packages()

    # Install packages from requirements.txt in a temporary virtual environment
    install_requirements()

    # Check if create_ap is already installed
    if is_create_ap_installed():
        logging.info("create_ap is already installed")
    else:
        # Prompt for access point functionality
        if get_user_confirmation("Do you want to install the access point functionality (create_ap)? This is a potential security risk and can be disabled later."):
            # Install create_ap
            install_create_ap()
        else:
            logging.info("Access point functionality will not be installed")

    # Enable I2C
    enable_i2c()

    # Blacklist sound module
    blacklist_sound_module()

    # Create startup script
    create_startup_script()

    # Update rc.local
    update_rc_local()

    # Copy config file
    config_source = os.path.join(thisPath, 'adeept_rasptank', 'server', 'config.txt')
    config_destination = '/etc/config.txt'
    try:
        if os.path.exists(config_source):
            logging.info(f"Copying config file from {config_source} to {config_destination}")
            run_command(f"sudo cp -f {config_source} {config_destination}")
        else:
            logging.warning(f"Config file not found at {config_source}. Skipping copy.")
    except Exception as e:
        logging.error(f"Error copying config file: {str(e)}")

    # Prompt for reboot confirmation
    if get_user_confirmation("The installation is complete. The Raspberry Pi will now reboot. Do you want to continue?"):
        logging.info('The program in Raspberry Pi has been installed, disconnected and restarted.')
        logging.info('You can now power off the Raspberry Pi to install the camera and driver board (Robot HAT).')
        logging.info('After turning on again, the Raspberry Pi will automatically run the program to set the servos port signal to turn the servos to the middle position, which is convenient for mechanical assembly.')
        logging.info('restarting...')
        
        # Restart the system
        run_command("sudo reboot", check=False)
    else:
        logging.info("Reboot cancelled by user.")

# Run the main function
if __name__ == "__main__":
    main()
