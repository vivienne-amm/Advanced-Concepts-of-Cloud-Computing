#!/bin/bash
# Script used to install and benchmark MySQL Standalone Server.

# Install MySQL Server and Sysbench
sudo apt-get update
sudo apt-get install mysql-server sysbench -y

cd home/ubuntu

# Download Sakila database
sudo wget https://downloads.mysql.com/docs/sakila-db.tar.gz -O /home/ubuntu/sakila-db.tar.gz
sudo tar -xvf /home/ubuntu/sakila-db.tar.gz -C /home/ubuntu/

# Upload Sakila database to MySQL
sudo mysql -u root -e "SOURCE /home/ubuntu/sakila-db/sakila-schema.sql;"
sudo mysql -u root -e "SOURCE /home/ubuntu/sakila-db/sakila-data.sql;"

# Benchmark using Sysbench using table size of 100 000, 6 threads and maximum time of 60 seconds
# Results can be found on the standalone instance at /home/ubuntu/results.txt
sudo sysbench oltp_read_write --table-size=100000 --mysql-db=sakila --mysql-user=root --db-driver=mysql prepare
sudo sysbench oltp_read_write --table-size=100000 --threads=6 --max-time=60 --max-requests=0 --mysql-db=sakila --db-driver=mysql --mysql-user=root  run > ./results.txt
sudo sysbench oltp_read_write --mysql-db=sakila --mysql-user=root --db-driver=mysql  --mysql-password=root cleanup

