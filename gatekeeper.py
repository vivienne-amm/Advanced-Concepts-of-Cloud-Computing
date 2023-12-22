import socket
import re


def is_valid_response(response):
    # Define a regex pattern based on the expected format
    pattern = re.compile(r'^(direct|custom|random)\|.*$', re.IGNORECASE)

    # Use the pattern to match against the response
    match = pattern.match(response)

    # If there is a match, the response is considered valid
    return bool(match)

def main():
    """Main."""

    host = '0.0.0.0'
    #Gate keeper port
    port = 5001

    s = socket.socket()
    print("socket created")
    s.bind((host, port))
    print("socket bound with host " + host)

    s.listen(1)  # Listen to one connection

    conn, addr = s.accept()
    print('connection from: ' + str(addr))

    trusted_socket = socket.socket()
    #proxy
    destination_ip = "172.31.1.10"
    dest_port = 5001
    trusted_socket.connect((destination_ip, dest_port))

    while True:
        data = conn.recv(2048)  # Max bytes
        response_decode = data.decode('utf-8').strip()
        if not data:
            break
        print('from connected user: ' + response_decode)

        if not is_valid_response(response_decode):
            break

        print("Connected to the trusted host!")
        trusted_socket.send(data)

        response_to_client = "Your message was received and processed successfully!"
        conn.send(response_to_client.encode('utf-8'))

    trusted_socket.close()
    s.close()
    print("sockets closed on proxy")

if __name__ == '__main__':
    main()

