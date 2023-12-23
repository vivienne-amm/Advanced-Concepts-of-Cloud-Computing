#!/bin/bash
# tutorial: https://www.digitalocean.com/community/tutorials/how-to-create-a-multi-node-mysql-cluster-on-ubuntu-18-04?fbclid=IwAR1m4Y8lPYDZzlpCKiSmsi4b-0roZPSidVfw1yO9dXrJ6YVcHc7Q2MKsVHY

# Install dependencies
sudo apt-get update
sudo apt-get install libncurses5 libclass-methodmaker-perl -y

# Download and install MySQL data node deamon
cd /home/ubuntu
wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-7.6/mysql-cluster-community-data-node_7.6.6-1ubuntu18.04_amd64.deb
sudo dpkg -i mysql-cluster-community-data-node_7.6.6-1ubuntu18.04_amd64.deb

# Specify the master node
echo "
[mysql_cluster]
ndb-connectstring=ip-172-31-1-1.ec2.internal
" | sudo tee /etc/my.cnf

# Creating data directory
sudo mkdir -p /usr/local/mysql/data

# Add  instructions for system to start, stop and restart ndb_mgmd
echo "
[Unit]
Description=MySQL NDB Data Node Daemon
After=network.target auditd.service

[Service]
Type=forking
ExecStart=/usr/sbin/ndbd
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=on-failure

[Install]
WantedBy=multi-user.target
" | sudo tee /etc/systemd/system/ndbd.service

# Reload systemd manager, enable ndb_mgmd and start ndb_mgmd
sudo systemctl daemon-reload
sudo systemctl enable ndbd
sudo systemctl start ndbd