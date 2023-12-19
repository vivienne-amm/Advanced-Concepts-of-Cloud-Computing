#!/usr/bin/python
"""Python module that sends TCP requests to AWS instance."""

import socket
import csv
import time
import os
import sys


if __name__ == '__main__':
    # Gatekeeper Id
    host = "172.31.1.11"
    port = 5001

    s = socket.socket()
    print("Socket created")

    s.connect((host, port))
    print("Connected to gatekeeper")


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

    # ask for user to enter query/queries in the terminal
    if len(sys.argv) < 3:
        sql_command = ""
        while True:
            line = input("> ")
            sql_command += line + "\n"
            if len(line) > 0 and line[-1] == ";":
                arguments = [type, sql_command]
                sendData = f"{type}|{sql_command}"
                print(sendData)

                s.send(str.encode(sendData))
                time.sleep(0.1)
                # s.send(str.encode("hello server!"))
                msg = s.recv(2048)
                print(msg)
                print(msg.decode())
                s.close();
                sql_command = ""
            if line.lower().count("exit") > 0:
                break


