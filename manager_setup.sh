sudo apt-get update
sudo apt-get install libncurses5 libaio1 libmecab2 sysbench -y
cd /home/ubuntu

# installing mysql cluster management server
wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-7.6/mysql-cluster-community-management-server_7.6.6-1ubuntu18.04_amd64.deb
sudo dpkg -i mysql-cluster-community-management-server_7.6.6-1ubuntu18.04_amd64.deb
rm mysql-cluster-community-management-server_7.6.6-1ubuntu18.04_amd64.deb

# adding sql cluster config file
sudo mkdir /var/lib/mysql-cluster

echo "[ndbd default]
# Options affecting ndbd processes on all data nodes:
NoOfReplicas=3	# Number of replicas

[ndb_mgmd]
# Management process options:
hostname=ip-172-31-1-1.ec2.internal # Hostname of the manager
datadir=/var/lib/mysql-cluster	# Directory for the log files
NodeId=1

[ndbd]
hostname=ip-172-31-1-2.ec2.internal # Hostname/IP of the first data node
NodeId=2			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[ndbd]
hostname=ip-172-31-1-3.ec2.internal # Hostname/IP of the second data node
NodeId=3			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[ndbd]
hostname=ip-172-31-1-4.ec2.internal # Hostname/IP of the third data node
NodeId=4			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files


[mysqld]
# SQL node options:
hostname=ip-172-31-1-1.ec2.internal # MySQL server/client on the same instance as the cluster manager
NodeId=11
"  | sudo tee /var/lib/mysql-cluster/config.ini

echo "
[Unit]
Description=MySQL NDB Cluster Management Server
After=network.target auditd.service

[Service]
Type=forking
ExecStart=/usr/sbin/ndb_mgmd -f /var/lib/mysql-cluster/config.ini
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=on-failure

[Install]
WantedBy=multi-user.target
" | sudo tee /etc/systemd/system/ndb_mgmd.service

sudo systemctl daemon-reload
sudo systemctl enable ndb_mgmd
sudo systemctl start ndb_mgmd


# Download MySQL Server
wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-7.6/mysql-cluster_7.6.6-1ubuntu18.04_amd64.deb-bundle.tar
mkdir install
tar -xvf mysql-cluster_7.6.6-1ubuntu18.04_amd64.deb-bundle.tar -C install/
cd install

# Install MySQL Server
sudo dpkg -i mysql-common_7.6.6-1ubuntu18.04_amd64.deb
sudo dpkg -i mysql-cluster-community-client_7.6.6-1ubuntu18.04_amd64.deb
sudo dpkg -i mysql-client_7.6.6-1ubuntu18.04_amd64.deb

# Configure installation to avoid using MySQL prompt
sudo debconf-set-selections <<< 'mysql-cluster-community-server_7.6.6 mysql-cluster-community-server/root-pass password root'
sudo debconf-set-selections <<< 'mysql-cluster-community-server_7.6.6 mysql-cluster-community-server/re-root-pass password root'

# Install the rest of the packages
sudo dpkg -i mysql-cluster-community-server_7.6.6-1ubuntu18.04_amd64.deb
sudo dpkg -i mysql-server_7.6.6-1ubuntu18.04_amd64.deb

# Configure client to connect to the master node
echo "
[mysqld]
# Options for mysqld process:
ndbcluster                      # run NDB storage engine
bind-address=0.0.0.0            # bind to all available addresses
ndb-connectstring=ip-172-31-1-1.ec2.internal  # location of management server

[mysql_cluster]
# Options for NDB Cluster processes:
ndb-connectstring=ip-172-31-1-1.ec2.internal  # location of management server
" | sudo tee -a /etc/mysql/my.cnf

# Restart MySQL Server
sudo systemctl restart mysql
sudo systemctl enable mysql