import socket
import re
import configparser

config = configparser.ConfigParser()
config.read('config.ini')


def is_valid_response(response):
    # Define a regex pattern based on the expected format
    pattern = re.compile(r'^(direct|custom|random)\|.*$', re.IGNORECASE)

    # Use the pattern to match against the response
    match = pattern.match(response)

    # If there is a match, the response is considered valid
    return bool(match)


def main():
    host = '0.0.0.0'
    port = int(config['Gatekeeper']['Port'])

    s = socket.socket()
    print("socket created")
    s.bind((host, port))
    print("socket bound with host " + host)

    # Listen for incoming connections
    s.listen(1)

    conn, addr = s.accept()
    print('connection from: ' + str(addr))

    trusted_socket = socket.socket()

    destination_ip = config['Proxy']['Host']
    dest_port = int(config['Proxy']['Port'])

    # Connect to the proxy
    trusted_socket.connect((destination_ip, dest_port))

    while True:
        # Receive data from the connected user
        data = conn.recv(2048)
        response_decode = data.decode('utf-8').strip()

        if not data:
            break

        print('from connected user: ' + response_decode)

        if not is_valid_response(response_decode):
            break

        print("Connected to the trusted host!")
        trusted_socket.send(data)

        # Send a response to the connected user
        response_to_client = "Your message was received and processed successfully!"
        conn.send(response_to_client.encode('utf-8'))

    trusted_socket.close()
    s.close()
    print("sockets closed on proxy")


if __name__ == '__main__':
    main()
