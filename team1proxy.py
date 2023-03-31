from socket import socket, AF_INET, SOCK_STREAM
from pathlib import Path

tcpServerSock = socket(AF_INET, SOCK_STREAM)
tcpServerSock.bind(("", 8888))
tcpServerSock.listen(1)

while True:
    # Start receiving data from the client
    print("Ready to serve...")

    tcpCLISock, addr = tcpServerSock.accept()
    print("Received a connection from:", addr)

    message = tcpCLISock.recv(4096).decode()
    # Extract the fileURL from the given message
    fileURL = message.split()[1].partition("/")[2]

    fileExist = False

    try:
        # Check wether the file exist in the cache
        f = open("cache/" + fileURL, "r")
        outputdata = f.readlines()
        f.close()

        fileExist = True

        headers = ["HTTP/1.1 200 OK\r\n", "Content-Type:text/html\r\n\r\n"]
        _ = list(map(lambda header: tcpCLISock.send(header.encode()), headers))
        _ = list(map(lambda line: tcpCLISock.send(line.encode()), outputdata))

        print("Read from cache")

    # Error handling for file not found in cache
    except IOError:
        if fileExist is False:
            # Create a socket on the proxyserver
            c = socket(AF_INET, SOCK_STREAM)

            try:
                # Connect to the socket to port 80
                hostname = fileURL.partition("/")[0]
                port = 80
                c.connect((hostname, port))

                path = fileURL.partition("/")[2]

                # Create a temporary file on this socket and ask port 80
                # for the file requested by the client
                fileObj = c.makefile("rwb", 0)
                headers = [f"GET /{path} HTTP/1.1\r\n", f"Host: {hostname}\r\n\r\n"]
                # Anything sent over the socket must be encoded.
                _ = list(map(lambda header: fileObj.write(header.encode()), headers))

                # Read the response into buffer
                buff = fileObj.read()
                # Extract file from raw data (by excluding header)
                requestedFile = buff.split(b"\r\n\r\n")[1]

                # Create a new file in the cache for the requested file.
                # Also send the response in the buffer to client socket and the
                # corresponding file in the cache

                # Save all files in folder named 'cache'
                fileURL = "cache/" + fileURL
                folders = fileURL.split("/")
                if len(folders) > 1:
                    folders = folders[0 : len(folders) - 1]
                    foldersPath = "/".join(folders)
                    Path(foldersPath).mkdir(parents=True, exist_ok=True)

                tmpFile = open(fileURL, "wb")
                tmpFile.write(requestedFile)
                tmpFile.close()

                headers = ["HTTP/1.1 200 OK\r\n", "Content-Type:text/html\r\n\r\n"]
                _ = list(map(lambda header: tcpCLISock.send(header.encode()), headers))

                tcpCLISock.send(requestedFile)

            except Exception:
                tcpCLISock.send("HTTP/1.0 500 Internal Server Error\r\n\r\n".encode())

            c.close()

        else:
            tcpCLISock.send("HTTP/1.0 404 Not Found\r\n\r\n".encode())

    # Cleaup, close the client and the server sockets, probably should have
    # this catch C-c
    tcpCLISock.close()

tcpServerSock.close()
