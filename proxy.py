#!/usr/bin/python
"""Python module that receives TCP requests."""
import re

import socket
import pymysql
import random
from pythonping import ping
from sshtunnel import SSHTunnelForwarder

ips = {
    'master': '172.31.1.1',
    'worker1': '172.31.1.2',
    'worker2': '172.31.1.3',
    'worker3': '172.31.1.4'
}

workers = ['worker1', 'worker2', 'worker3']

# Params to setup the SSH tunnel forwarder
ssh_config = {
    'ssh_username': 'ubuntu',
    'ssh_pkey': 'vockey.pem',
    'remote_bind_address': (ips["master"], 3306),
}

# Params to connect to the MySQL cluster
db_config = {
    'host': ips["master"],
    'user': 'user',
    'password': 'password',
    'db': 'sakila',
    'port': 3306,
    'autocommit': True
}

def get_fastest_worker():
    fastest_worker = ""
    time = 2000
    for worker in workers:
        ping_result = ping(ips[worker], count=1, timeout=2)
        if ping_result.packet_loss != 1 and time > ping_result.rtt_avg_ms:
            fastest_worker = worker
            time = ping_result.rtt_avg_ms
    print("Best one was  " + fastest_worker)

    return fastest_worker

def direct(query):
    print("Proxy Type: direct")
    execute_commands("master", query)

def randomized(query):
    print("Proxy Type: ranomized")

    if not needs_write_access(query):
        random_worker = random.choice(workers)
        print("read on " + random_worker)
        execute_commands(random_worker, query)
    else:
        print("Needs write access therefore executed directly")
        direct(query)

def customized(query):
    print("Proxy Type: customized")

    if not needs_write_access(query):
        fastestWorker = get_fastest_worker()
        if fastestWorker != "":
            print("read on " + fastestWorker)
            execute_commands(fastestWorker, query)
    else:
        direct(query)

def needs_write_access(query):
    instructions = query.split(";")
    for instruction in instructions:
        keyword = instruction.strip().lower().split()
        if len(keyword) > 0 and keyword[0] in ["delete", "update", "create", "insert", "grant", "revoke"]:
            return True
    return False

def execute_commands(name, commands):
    """
    Runs the sql commands on the specified node.
    Prints the output of the command

    :param: name of the node
    :param: query to check
    """
    with SSHTunnelForwarder(ips[name], **ssh_config) as tunnel:
        print("executing on " + name + "with IP: " + ips[name])
        connection = pymysql.connect(**db_config)

        try:
            with connection.cursor() as cursor:
                print("Executing query: ", commands)

                cursor.execute(commands)

                if cursor.description is not None:
                    # Fetch the results of the query
                    result = cursor.fetchall()

                    # Print the results
                    print(tuple([i[0] for i in cursor.description]))
                    for line in result:
                        print(line)
        finally:
            # Close the connection to the MySQL cluster
            connection.close()


# route every POST requests to direct(), regardless of the path (equivalent to a wildcard)
def send_query(type, query):
    """
    Runs the sql commands

    :param: type of strategy used
    :param: query to run
    """
    type = str(type).strip()
    query = str(query).strip()

    if type == "custom":
        customized(query)
    elif type == "random":
        randomized(query)
    else:
        direct(query)


def extract_response_values(data):
    data = data.decode('utf-8').strip()

    # Define a regex pattern based on the expected format
    pattern = re.compile(r'^(direct|custom|random)\|(.*)$', re.IGNORECASE)

    # Use the pattern to match against the response
    match = pattern.match(data)

    # If there is a match, extract the values and return them
    if match:
        proxy_type, sql_command = match.groups()
        print("proxy_type" + proxy_type)
        print("sql command" + sql_command)

        return proxy_type, sql_command
    else:
        print("return none,none bevause no regex match")
        return None, None

def main():
    #proxy port
    port = 5001

    s = socket.socket()
    s.bind(('0.0.0.0', port))
    print("socket bound")

    s.listen(1)  # Listen to one connection
    conn, addr = s.accept()
    print('connection from: ' + str(addr))

    while True:
        data = conn.recv(409600)  # Max bytes
        print('Data: ' + str(data))

        proxy_type, sql_command = extract_response_values(data)

        if proxy_type is not None and sql_command is not None:
            print(f"Proxy Type: {proxy_type}")
            print(f"SQL Command: {sql_command}")
            send_query(proxy_type, sql_command)
            #response = "Processed successfully!"
            #s.send(str.encode(response))

        else:
            print("Invalid response!")

    s.close()
    print("socket closed on proxy")

if __name__ == '__main__':
    main()


