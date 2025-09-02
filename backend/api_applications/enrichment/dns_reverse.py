import socket


def get_domain(ip):

    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname

    except socket.herror:
        return None
