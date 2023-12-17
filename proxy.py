import pymysql
import sys
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
    'user': 'proxy_user',
    'password': 'super_secret_proxy_password',
    'db': 'mycluster',
    'port': 3306,
    'autocommit': True
}


def getLowestPingWorker():
    """
    Returns the name of the fastest worker

    :return name of worker with the lowest ping
    """
    best = ""
    time = 2000
    for worker in workers:
        ping_result = ping(ips[worker], count=1, timeout=2)
        if ping_result.packet_loss != 1 and time > ping_result.rtt_avg_ms:
            best = worker
            time = ping_result.rtt_avg_ms
    print("Best one was  " + best)

    return best


def needsWriteAccess(query):
    """
    Checks if a query needs write access.

    :param: query to check
    :return true if query needs write access, false otherwise.
    """
    instructions = query.split(";")
    for instruction in instructions:
        keyword = instruction.strip().lower().split()
        if len(keyword) > 0 and keyword[0] in ["delete", "update", "create", "insert", "grant", "revoke"]:
            return True
    return False


def executeCommands(name, commands):
    """
    Runs the sql commands on the specified node.
    Prints the output of the command

    :param: name of the node
    :param: query to check
    """
    with SSHTunnelForwarder(ips[name], **ssh_config) as tunnel:
        print("executing on " + ips[name])
        connection = pymysql.connect(**db_config)

        try:
            with connection.cursor() as cursor:
                # Execute a MySQL query
                sql = 'SELECT * FROM actor LIMIT 10;'
                cursor.execute(commands)

                # Fetch the results of the query
                result = cursor.fetchall()

                # Print the results
                print(tuple([i[0] for i in cursor.description]))
                for line in result:
                    print(line)
        finally:
            # Close the connection to the MySQL cluster
            connection.close()


def direct(query):
    """
    Runs the sql commands on direct strategy

    :param: query to run
    """
    print("directly")
    executeCommands("master", query)


def randomized(query):
    """
    Runs the sql commands on random strategy

    :param: query to run
    """
    print("ranomized")
    print("needsWriteAccess(query): " + str(needsWriteAccess(query)))

    if not needsWriteAccess(query):
        random_worker = random.choice(workers)
        print("read on " + random_worker)
        executeCommands(random_worker, query)
    else:
        print("Need Write access therefore exxecuted directly")
        direct(query)


def customized(query):
    """
    Runs the sql commands on custom strategy

    :param: query to run
    """
    print("customized")

    if not needsWriteAccess(query):
        fastestWorker = getLowestPingWorker()
        if fastestWorker != "":
            print("read on " + fastestWorker)
            executeCommands(fastestWorker, query)
    else:
        direct(query)


# route every POST requests to direct(), regardless of the path (equivalent to a wildcard)
def sendQuery(type, query):
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


if __name__ == "__main__":
    # if the first argument isn't specified, ask user to chose a proxy type
    type = ""
    if len(sys.argv) == 1:
        print("choose a proxy type:")
        print("-- (1) direct - default")
        print("-- (2) random")
        print("-- (3) custom")
        type = input(">>> ")

    # if the first argument is specified, use it as the proxy type
    if len(sys.argv) > 1:
        type = sys.argv[1]
        print('type > 1!')

    if type in ["2", "random"]:
        type = "random"
        print('type random')

    elif type in ["3", "custom"]:
        type = "custom"
        print('type custom')

    else:
        type = "direct"
        print('type direct')


    # if the second argument isn't specified, ask for user to enter query/queries in the terminal
    if len(sys.argv) < 3:
        print('type < 3!')
        text = ""
        while True:
            line = input("> ")
            text += line + "\n"
            if len(line) > 0 and line[-1] == ";":
                sendQuery(type, text)
                text = ""
            if line.lower().count("exit") > 0:
                break

    # if the second argument is specified, run the commands in the file if possible
    if len(sys.argv) == 3:
        print('type == 3!')
        with open(sys.argv[2]) as file:
            sendQuery(type, file.read())

