# LOG8415_TP3

https://www.digitalocean.com/community/tutorials/how-to-create-a-multi-node-mysql-cluster-on-ubuntu-18-04

To run the code following steps need to be executed:

1. connect to master with ssh and execute manager_setup on it 
2. connect to workers with ssh and execute worker_setup1 on it
3. run_benchmark script (on master?) 
3. connect to standalone with ssh and execute standalone_setup on it

- Make sure you have a python3 executable on your machine. You will also need 3 python libraries - boto3, requests and python-dotenv. If you are missing them you can use command pip install -r main_req.txt to install them.
- Create an .env file with your AWS credentials. An example with the valid format can seen in the .env.example file.
- Use main.py to initialize python3 main.py UP, tear down python3 main.py DOWN, or run a workload on the architecture python3 main.py RUN.

ssh -v -i /Users/vivi/Downloads/vockey.pem ubuntu@ec2-44-192-97-48.compute-1.amazonaws.com
