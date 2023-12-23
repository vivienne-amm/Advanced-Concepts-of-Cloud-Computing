import socket
import time
import sys
import configparser

# Read configuration from 'config.ini' file
config = configparser.ConfigParser()
config.read('config.ini')


def get_proxy_type():
    # If the proxy type is not provided as a command line argument,
    # prompt the user to select a proxy type.
    proxy_type = ""
    if len(sys.argv) == 1:
        print("Select a proxy type by entering the number or the proxy type name:")
        print("1) direct (default)")
        print("2) random")
        print("3) custom")
        proxy_type = input("proxy type: >> ")

        proxy_type = validate_user_input(proxy_type)

    # If the proxy type is provided as a command line argument, use it.
    elif len(sys.argv) > 1:
        proxy_type = validate_user_input(sys.argv[1])

    return proxy_type


def validate_user_input(user_input):
    # Validate user input for proxy type selection.
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
    # Prepare and send data to the gatekeeper.
    data_to_send = f"{proxy_type}|{sql_command}"
    print("Sending data")
    socket.send(str.encode(data_to_send))
    print("Data sent")

    time.sleep(0.1)
    received_msg = socket.recv(2048)
    print("Message received")
    print(received_msg.decode())


if __name__ == '__main__':
    host = config['Gatekeeper']['Host']
    port = int(config['Gatekeeper']['Port'])

    s = socket.socket()
    print("Socket created")

    s.connect((host, port))
    print("Connected to gatekeeper")

    proxy_type = get_proxy_type()
    # If SQL commands are not provided as command line arguments, prompt the user.
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

    # Close the socket connection.
    s.close()
