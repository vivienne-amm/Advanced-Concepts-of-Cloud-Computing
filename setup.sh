#!/bin/bash

  sudo yum update -y
  sudo amazon-linux-extras install mysql8.0 -y
  sudo yum install mysql-server -y
  sudo systemctl start mysqld
  sudo mysql_secure_installation