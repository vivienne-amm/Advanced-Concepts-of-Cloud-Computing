#!/usr/bin/python
"""Python module that sends TCP requests to AWS instance."""

import socket
import time
import sys
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

def get_proxy_type():
    # if the first argument is specified, use it as the proxy type
    proxy_type = ""
    if len(sys.argv) == 1:
        print("Select a proxy type by entering the number or the proxy type name:")
        print("1) direct (default)")
        print("2) random")
        print("3) custom")
        proxy_type = input("proxy type: >> ")

        proxy_type = validate_user_input(proxy_type)

    elif len(sys.argv) > 1:
        proxy_type = validate_user_input(sys.argv[1])

    return proxy_type

def validate_user_input(user_input):
    valid_types = {"1": "direct", "2": "random", "3": "custom"}
    default_type = "direct"

    if user_input.lower() in valid_types.values():
        return user_input.lower()
    elif user_input in valid_types:
        return valid_types[user_input]
    else:
        print(f"Invalid input. Defaulting to '{default_type}'.")
        return default_type

def send_data_to_gatekeeper(socket, proxy_type, sql_command):
    data_to_send = f"{proxy_type}|{sql_command}"
    print("Sending data")
    socket.send(str.encode(data_to_send))
    print("Data sent")

    time.sleep(0.1)
    received_msg = socket.recv(2048)
    print("Message received")
    print(received_msg.decode())

if __name__ == '__main__':
    # Gatekeeper Id
    host = config['Gatekeeper']['Host']
    port = int(config['Gatekeeper']['Port'])

    s = socket.socket()
    print("Socket created")

    s.connect((host, port))
    print("Connected to gatekeeper")

    proxy_type = get_proxy_type()
    # ask the user to enter queries in the terminal
    if len(sys.argv) < 3:
        sql_command = ""
        while True:
            print("Enter an SQL command or 'proxy' to change the proxy type:")
            line = input("> ")
            if line.lower() == "proxy":
                proxy_type = get_proxy_type()
            elif len(line) > 0 and line[-1] == ";":
                sql_command += line + "\n"
                send_data_to_gatekeeper(s, proxy_type, sql_command)
                sql_command = ""
            elif line.lower().count("exit") > 0:
                break

    s.close()

