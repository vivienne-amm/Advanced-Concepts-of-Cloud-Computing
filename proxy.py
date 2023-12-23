import re
import configparser
import socket
import pymysql
import random
from pythonping import ping
from sshtunnel import SSHTunnelForwarder

config = configparser.ConfigParser()
config.read('config.ini')

workers = ['Worker1', 'Worker2', 'Worker3']

# Setup parameters SSH tunnel forwarder
ssh_config = {
    'ssh_username': 'ubuntu',
    'ssh_pkey': 'vockey.pem',
    'remote_bind_address': (config['Master']['Host'], 3306),
}

# MySQL cluster connection parameters
db_config = {
    'host': config['Master']['Host'],
    'user': 'user',
    'password': 'password',
    'db': 'sakila',
    'port': 3306,
    'autocommit': True
}


def get_fastest_worker():
    # Find the fastest worker node based on ping response time
    fastest_worker = ""
    time = 2000
    for worker in workers:
        ping_result = ping(config[worker]['Host'], count=1, timeout=2)
        if ping_result.packet_loss != 1 and time > ping_result.rtt_avg_ms:
            fastest_worker = worker
            time = ping_result.rtt_avg_ms
    print("Fastest worker was  " + fastest_worker)

    return fastest_worker


def direct(query):
    # Execute query directly on the master node
    print("Proxy Type: direct")
    run_commands("Master", query)


def random(query):
    # Execute query on a randomly selected worker node or directly if it needs write access
    print("Proxy Type: randomized")

    if not needs_write_access(query):
        random_worker = random.choice(workers)
        print("read on " + random_worker)
        run_commands(random_worker, query)
    else:
        print("Needs write access therefore executed directly")
        direct(query)


def custom(query):
    # Execute query on a on fastest selected worker node or on master if it needs write access
    print("Proxy Type: customized")

    if not needs_write_access(query):
        fastestWorker = get_fastest_worker()
        if fastestWorker != "":
            print("read on " + fastestWorker)
            run_commands(fastestWorker, query)
    else:
        direct(query)


def needs_write_access(query):
    # Check if the query requires write access
    keywords = [instruction.strip().lower().split()[0] for instruction in query.split(";") if instruction.strip()]
    return any(keyword in ["delete", "update", "create", "insert", "grant", "revoke"] for keyword in keywords)


def run_commands(name, commands):
    with SSHTunnelForwarder(config[name]['Host'], **ssh_config) as tunnel:
        print("executing on " + name + "with IP: " + config[name]['Host'])
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


def send_query(type, query):
    type = str(type).strip()
    query = str(query).strip()

    if type == "custom":
        custom(query)
    elif type == "random":
        random(query)
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
        print("return none,none because no regex match")
        return None, None


def main():
    port = int(config['Proxy']['Port'])

    s = socket.socket()
    s.bind(('0.0.0.0', port))
    print("socket bound")

    s.listen(1)  # Listen to one connection
    conn, addr = s.accept()
    print('connection from: ' + str(addr))

    while True:
        data = conn.recv(2048)  # Max bytes
        print('Data: ' + str(data))

        proxy_type, sql_command = extract_response_values(data)

        if proxy_type is not None and sql_command is not None:
            print(f"Proxy Type: {proxy_type}")
            print(f"SQL Command: {sql_command}")
            send_query(proxy_type, sql_command)
        else:
            print("Invalid response!")

    s.close()
    print("socket closed on proxy")


if __name__ == '__main__':
    main()
