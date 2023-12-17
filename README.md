# LOG8415_TP3

https://www.digitalocean.com/community/tutorials/how-to-create-a-multi-node-mysql-cluster-on-ubuntu-18-04

To run the code following steps need to be executed:

1. connect to master with ssh and execute manager_setup on it 
2. connect to workers with ssh and execute worker_setup1 on it
3. benchmark script (on master?) 
3. connect to standalone with ssh and execute standalone_setup on it

- Make sure you have a python3 executable on your machine. You will also need 3 python libraries - boto3, requests and python-dotenv. If you are missing them you can use command pip install -r main_req.txt to install them.
- Create an .env file with your AWS credentials. An example with the valid format can seen in the .env.example file.
- Use main.py to initialize python3 main.py UP, tear down python3 main.py DOWN, or run a workload on the architecture python3 main.py RUN.

ssh -v -i /Users/vivi/Downloads/vockey.pem ubuntu@ec2-44-211-49-109.compute-1.amazonaws.com

scp -r -i /Users/vivi/Downloads/vockey.pem proxy.py ubuntu@ec2-44-193-10-101.compute-1.amazonaws.com:/home/ubuntu

scp -r -i /Users/vivi/Downloads/vockey.pem sql_examples/create_test.sql ubuntu@ec2-3-231-156-110.compute-1.amazonaws.com:/home/ubuntu

Send To Proxy:
scp -r -i /Users/vivi/Downloads/vockey.pem . ubuntu@ec2-44-211-49-109.compute-1.amazonaws.com:/home/ubuntu
scp -r -i /Users/vivi/Downloads/vockey.pem /Users/vivi/Downloads/vockey.pem ubuntu@ec2-44-211-49-109.compute-1.amazonaws.com:/home/ubuntu



On master node:
mysql -u root -p

(passwort ist root)
DROP SCHEMA IF EXISTS mycluster;
CREATE SCHEMA mycluster;
CREATE USER 'proxy_user'@'%' IDENTIFIED BY 'super_secret_proxy_password';
GRANT ALL PRIVILEGES ON mycluster.* TO 'proxy_user'@'%';
FLUSH PRIVILEGES;

copy things of create_test sql and let it run on mysql on maste node


Dann auf proxy starten z.B. mit  
sudo /home/ubuntu/venv/bin/python3 proxy.py "custom"
und dann z.B.:
SELECT * FROM actor LIMIT 5;