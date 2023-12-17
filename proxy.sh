"""#!/bin/bash
#Script used to install proxy application on Proxy instance.
# Install Python, Pip and Git
apt-get update
apt-get install python3 python3-pip git -y

# Install Python libraries needed to run application
pip install sshtunnel pythonping pymysql pandas argparse

# Clone project where the proxy application is found
git clone https://github.com/bourret27/LOG8415-FinalProject.git
"""

#!/bin/bash
# user data file for cluster proxy
sudo apt-get update -y
sudo apt-get install python3-venv nginx dos2unix -y

# fetching config files from git
cd /home/ubuntu

chmod 400 vockey.pem

# adding service file
#cp /home/ubuntu/8415_Project/proxy.service /etc/systemd/system

# setup python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

