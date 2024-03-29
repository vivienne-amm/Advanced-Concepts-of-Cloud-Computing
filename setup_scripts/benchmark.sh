#!/bin/bash
# MySQL Cluster Benchmark Script execute after manager and worker setups are completed
# Download Sakila database
cd /home/ubuntu
wget https://downloads.mysql.com/docs/sakila-db.tar.gz -O /home/ubuntu/sakila-db.tar.gz
tar -xvf /home/ubuntu/sakila-db.tar.gz -C /home/ubuntu/

# Upload Sakila database to MySQL
mysql -u root -proot -e "SOURCE /home/ubuntu/sakila-db/sakila-schema.sql;"
mysql -u root -proot -e "SOURCE /home/ubuntu/sakila-db/sakila-data.sql;"

# Benchmark using Sysbench
# Configuration: Table size of 100,000, 6 threads, and maximum time of 60 seconds
# Writing results in /home/ubuntu/results.txt
sysbench oltp_read_write --table-size=100000 --mysql-db=sakila --mysql-user=root --mysql-password=root --db-driver=mysql prepare
sysbench oltp_read_write --table-size=100000 --threads=6 --time=60 --max-requests=0 --mysql-db=sakila --mysql-user=root --mysql-password=root --db-driver=mysql run > /home/ubuntu/results.txt
sysbench oltp_read_write --mysql-db=sakila --mysql-user=root --mysql-password=root --db-driver=mysql cleanup