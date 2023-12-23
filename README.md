# Final Project: Advanced Concepts of Cloud Computing (LOG8415)
Vivienne Amm, 2310805

This is the final project _Scaling Databases and Implementing Cloud Design Patterns_ created for the course _Advanced Concepts of Cloud Computing_ at Polytechnique Montreal in Fall Trimester 2023.
### Initializing the architecture
- Make sure you have a python3 executable on your machine. You will also need the python libraries boto3 and python-dotenv. If you are missing them execute the command `pip install -r main_req.txt`.
- Create an `.env` file with your AWS credentials. An example with the valid format can seen in the `.env.example` file.
- Run `find . -type f -name "*.sh" -exec chmod +x {} ＼;`  in the setup_scripts directory: 
- Use `main.py UP` to initialize the architecture.
- Connect to the Proxy and the Gatekeeper instances with ssh and execute the commands from the `setup_scripts/proxy_gatekeeper.sh` file on it.

To SSH onto an instance adapt the following command:
`ssh -v -i <PATH_TO_VOCKEY.PEM_ON_LOCAL_MACHINE> ubuntu@<INSTANCE_DNS>`

### Benchmarking MySQL Standalone vs MySQL Cluster
The sysbench tool is used to conduct a read-write 60-second benchmark with 6 threads on the MySQL _sakila_ database with a table size of 100,000 records.
- **Standalone instance**: the benchmark is run automatically on initialization of the instance (using the standalone_setup.sh script in the Userdata). 
   - The benchmark results can be found on the Standalone instance at `/home/ubuntu/results.txt`.
- **MySQL cluster**: execute the commands of the `setup_scripts/benchmark.sh` script on the master instance to run the benchmark.
   - The benchmark results can be found on the Master instance at `/home/ubuntu/results.txt`.


### Testing the proxy and gatekeeper
1. SSH on the **master** instance and execute the following commands:
    - `mysql -u root -p`
      - This will prompt you to enter a password. The password is "root".
    - `USE sakila; `
    - `CREATE USER 'user'@'%' IDENTIFIED BY 'password';`
    - `GRANT ALL PRIVILEGES ON sakila.* TO 'user'@'%'; `
    - `FLUSH PRIVILEGES;`
2. SSH on the **proxy** instance and execute the following command:
    - `sudo /home/ubuntu/venv/bin/python3 proxy.py`
3. SSH on the **gatekeeper** instance and execute the following command:
    - `sudo /home/ubuntu/venv/bin/python3 gatekeeper.py`
4. Run `python3 client.py`
    - This will prompt you to enter the proxy method you want to use (direct/ random/ custom) and will ask you to enter an SQL command.

### Example SQL commands for demonstration: 
As example, the actor table of the sakila database (or any other table defined in the sakila) can be used.
Following are some example SQL commands that can be entered after starting client.py:

#### SELECT:
- `SELECT * FROM actor ORDER BY actor_id DESC LIMIT 5;`

#### INSERT:
- `SELECT * FROM actor ORDER BY actor_id DESC LIMIT 5;`
- `INSERT INTO actor(first_name, last_name) VALUES ("MARGOT", "ROBBIE");`
- `SELECT * FROM actor ORDER BY actor_id DESC LIMIT 5;`

#### UPDATE:
- `SELECT * FROM actor WHERE last_name="REYNOLDS";`
- `UPDATE actor SET first_name="Ryan" WHERE actor_id=135;`
- `SELECT * FROM actor WHERE last_name="REYNOLDS";`

### Tearing down the architecture
- At the end, tear down the architecture using `python3 main.py DOWN`.
- Don't forget to end the AWS session.
