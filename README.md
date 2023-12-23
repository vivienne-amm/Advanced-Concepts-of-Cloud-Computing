# LOG8415_TP3

https://www.digitalocean.com/community/tutorials/how-to-create-a-multi-node-mysql-cluster-on-ubuntu-18-04

To run the code following steps need to be executed:

1. run in directory: find . -type f -name "*.sh" -exec chmod +x {} \;
connect to master with ssh and execute manager_setup on it 
2. connect to workers with ssh and execute worker_setup1 on it
3. benchmark script (on master?) 
3. connect to standalone with ssh and execute standalone_setup on it

- Make sure you have a python3 executable on your machine. You will also need 3 python libraries - boto3 and python-dotenv. If you are missing them you can use command pip install -r main_req.txt to install them.
- Create an .env file with your AWS credentials. An example with the valid format can seen in the .env.example file.
- Use main.py to initialize python3 main.py UP, tear down python3 main.py DOWN, or run a workload on the architecture python3 main.py RUN.

#gatekeeper
ec2-3-222-177-119
ssh -v -i /Users/vivi/Downloads/vockey.pem ubuntu@ec2-3-222-177-119.compute-1.amazonaws.com


#proxy
ec2-3-239-150-182
ssh -v -i /Users/vivi/Downloads/vockey.pem ubuntu@ec2-3-239-150-182.compute-1.amazonaws.com

#manager
ec2-3-235-250-7
ssh -v -i /Users/vivi/Downloads/vockey.pem ubuntu@ec2-3-235-250-7.compute-1.amazonaws.com

#workers
ec2-18-234-139-173
ec2-3-235-3-140
ec2-44-200-133-26

ssh -v -i /Users/vivi/Downloads/vockey.pem ubuntu@ec2-44-222-68-148.compute-1.amazonaws.com

scp -r -i /Users/vivi/Downloads/vockey.pem gatekeeper.py ubuntu@ec2-3-237-61-24.compute-1.amazonaws.com:/home/ubuntu

scp -r -i /Users/vivi/Downloads/vockey.pem sql_examples/create_test.sql ubuntu@ec2-44-197-194-245.compute-1.amazonaws.com:/home/ubuntu

Send To Proxy:ec2-44-204-211-99
scp -r -i /Users/vivi/Downloads/vockey.pem . ubuntu@ec2-44-204-211-99.compute-1.amazonaws.com:/home/ubuntu

#proxy
ec2-3-235-166-251
scp -r -i /Users/vivi/Downloads/vockey.pem . ubuntu@ec2-3-235-166-251.compute-1.amazonaws.com:/home/ubuntu
scp -r -i /Users/vivi/Downloads/vockey.pem /Users/vivi/Downloads/vockey.pem ubuntu@ec2-3-235-166-251.compute-1.amazonaws.com:/home/ubuntu

#gatekeeper
ec2-3-222-177-119
scp -r -i /Users/vivi/Downloads/vockey.pem . ubuntu@ec2-44-222-68-148.compute-1.amazonaws.com:/home/ubuntu
scp -r -i /Users/vivi/Downloads/vockey.pem /Users/vivi/Downloads/vockey.pem ubuntu@ec2-44-222-68-148.compute-1.amazonaws.com:/home/ubuntu


On master node:
mysql -u root -p

(passwort ist root)
DROP SCHEMA IF EXISTS mycluster;
CREATE SCHEMA mycluster;
USE mycluster;

CREATE USER 'proxy_user'@'%' IDENTIFIED BY 'super_secret_proxy_password';
GRANT ALL PRIVILEGES ON mycluster.* TO 'proxy_user'@'%'; # oder mycluster statt mycluster
FLUSH PRIVILEGES;

copy things of create_test sql and let it run on mysql on maste node

Dann auf proxy starten z.B. mit  
sudo /home/ubuntu/venv/bin/python3 proxy.py "custom"
und dann z.B.:
SELECT * FROM actor LIMIT 5;

sudo /home/ubuntu/venv/bin/python3 proxy.py

On gatekeeper:
sudo /home/ubuntu/venv/bin/python3 gatekeeper.py
sudo /home/ubuntu/venv/bin/python3 client.py

USE saklia;

CREATE USER 'user'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON sakila.* TO 'user'@'%'; 
FLUSH PRIVILEGES;

Insert:
SELECT * FROM actor ORDER BY actor_id DESC LIMIT 10;
INSERT INTO actor(first_name, last_name) VALUES ("EMMA", "WATSON"), ("SCARLETT", "JOHANSSON");
SELECT * FROM actor ORDER BY actor_id DESC LIMIT 10;

Update
SELECT * FROM actor WHERE last_name="KILMER";
UPDATE actor SET first_name="test" WHERE actor_id=162;
SELECT * FROM actor WHERE last_name="KILMER";