from errno import errorcode

import pymysql
import sys
import random
import socket

from pythonping import ping

def initialize_socket():
    s = socket.socket()
    print("Socket successfully created")

    # proxy port
    port = 5001
    s.bind(('', port))
    print("socket binded to %s" % (port))

    s.listen(1)
    print("socket is listening")

    return s

ips = {
    'master': '137.31.1.1',
    'worker1': '137.31.1.2',
    'worker2': '137.31.1.3',
    'worker3': '137.31.1.4'
}

workers = ['worker1', 'worker2', 'worker3']
master = 'master'

def getFastestPingWorker():
    """
    Returns the name of the fastest worker

    :return name of worker with the fastest ping
    """
    best_server = workers[0]
    time = 1000
    for worker in workers:
        ping_result = ping(ips[worker], count=1, timeout=5)
        if not(ping_result.packet_loss) and time > ping_result.rtt_avg_ms:
            best_server = worker
            time = ping_result.rtt_avg_ms
    return best_server


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


def executeCommands(server_name, commands):
    """
    Runs the sql commands on the specified node.
    Prints the output of the command

    :param: name of the node
    :param: query to check
    """
    try:
        cnx = pymysql.connector.connect(user='proxy', password='1234',
                                      host=ips[server_name],
                                      database='mycluster')
    except pymysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    cursor = cnx.cursor()
    cursor.execute(commands)
    cmd_type = commands.split()[0].lower()
    if cmd_type == "insert" or cmd_type == "delete":
        cnx.commit()
    elif cmd_type == "select":
        print("query result: ")
        print(cursor.fetchall())

def direct(query):
    """
    Runs the sql commands on direct strategy

    :param: query to run
    """
    executeCommands("master", query)
    print("direct hit, request handled by Master\n")


def randomized(query):
    """
    Runs the sql commands on random strategy

    :param: query to run
    """
    if not needsWriteAccess(query):
        random_worker = random.choice(workers)
        print("read on " + random_worker)
        executeCommands(random_worker, query)
        print("random, request handled by " + random_worker + "\n")
    else:
        direct(query)


def customized(query):
    """
    Runs the sql commands on custom strategy

    :param: query to run
    """
    if not needsWriteAccess(query):
        fastestWorker = getFastestPingWorker()
        if fastestWorker != "":
            print("read on " + fastestWorker)
            executeCommands(fastestWorker, query)
            print("customized, request handled by the fastest worker: " + fastestWorker + "\n")

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

    if type in ["2", "random"]:
        type = "random"
    elif type in ["3", "custom"]:
        type = "custom"
    else:
        type = "direct"

    # if the second argument isn't specified, ask for user to enter query/queries in the terminal
    if len(sys.argv) < 3:
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
        with open(sys.argv[2]) as file:
            sendQuery(type, file.read())

