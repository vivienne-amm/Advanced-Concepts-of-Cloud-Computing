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

    # read values from a section
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

    trustedSocket = socket.socket()
    #proxy
    destIp = "172.31.1.10"
    destPort = 5001
    trustedSocket.connect((destIp, destPort))

    while True:
        data = conn.recv(409600)  # Max bytes
        responseDecode = data.decode('utf-8').strip()
        print("responseDecode")
        print(responseDecode)
        if not data:
            break
        print('from connected user: ' + responseDecode)

        if not is_valid_response(responseDecode):
            break

        print("Connected to the trusted host!")
        trustedSocket.send(data)

        response_to_client = "Your message was received and processed successfully!"
        conn.send(response_to_client.encode('utf-8'))

    trustedSocket.close()
    s.close()
    print("sockets closed on proxy")

if __name__ == '__main__':
    main()

