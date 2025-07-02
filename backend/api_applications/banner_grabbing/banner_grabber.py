import logging
import socket
import ssl


def get_banner(target_ip, target_port):

    socket.setdefaulttimeout(2)
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        banner_data = ""

        if target_port == 22:  # SSH
            sock.connect((target_ip, target_port))
            banner_data = sock.recv(1024).decode("utf-8", errors="ignore")
            if banner_data.strip().startswith("SSH-"):
                return f"SSH:\n{banner_data.strip()}"
            else:
                return f"SSH (Unrecognized): {banner_data.strip()}"

        elif target_port == 21:  # FTP
            sock.connect((target_ip, target_port))
            banner_data = sock.recv(1024).decode("utf-8", errors="ignore")
            if banner_data.strip().startswith("220"):
                return f"FTP:\n{banner_data.strip()}"
            else:
                return f"FTP (Unrecognized): {banner_data.strip()}"

        elif (
            target_port == 25 or target_port == 587
        ):  # SMTP (25 for sending, 587 for submission)
            sock.connect((target_ip, target_port))
            initial_banner = sock.recv(1024).decode("utf-8", errors="ignore")
            if initial_banner.strip().startswith("220"):
                sock.sendall(b"EHLO test\r\n")
                ehlo_response = sock.recv(4096).decode("utf-8", errors="ignore")
                return f"SMTP:\n{initial_banner.strip()}\n{ehlo_response.strip()}"
            else:
                return f"SMTP (Unrecognized): {initial_banner.strip()}"

        elif target_port == 80:  # HTTP
            sock.connect((target_ip, target_port))
            request = f"HEAD / HTTP/1.1\r\nHost: {target_ip}\r\nUser-Agent: BannerGrabber/1.0\r\nConnection: close\r\n\r\n"
            sock.sendall(request.encode("utf-8"))
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                banner_data += data.decode("utf-8", errors="ignore")
                if "\r\n\r\n" in banner_data:  # Stop after header section
                    break
            lines = banner_data.split("\r\n")
            http_banner_lines = [
                line
                for line in lines
                if line.strip().startswith(
                    ("HTTP/", "Server:", "Content-Type:", "Location:", "X-Powered-By:")
                )
            ]
            if http_banner_lines:
                return f"HTTP:\n{(http_banner_lines)}"
            else:
                return "HTTP (No server banner in headers)."

        elif target_port == 443:  # HTTPS
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=target_ip)
            sock.connect((target_ip, target_port))

            request = f"HEAD / HTTP/1.1\r\nHost: {target_ip}\r\nUser-Agent: BannerGrabber/1.0\r\nConnection: close\r\n\r\n"
            sock.sendall(request.encode("utf-8"))
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                banner_data += data.decode("utf-8", errors="ignore")
                if "\r\n\r\n" in banner_data:
                    break
            lines = banner_data.split("\r\n")
            http_banner_lines = [
                line
                for line in lines
                if line.strip().startswith(
                    ("HTTP/", "Server:", "Content-Type:", "Location:", "X-Powered-By:")
                )
            ]
            if http_banner_lines:
                return f"HTTPS:\n{(http_banner_lines)}"
            else:
                return "HTTPS (No server banner in headers)."

        else:
            # Generic attempt for other ports or services
            sock.connect((target_ip, target_port))
            banner_data = sock.recv(4096).decode("utf-8", errors="ignore")
            if banner_data.strip():
                return f"Generic/Unknown Service:\n{banner_data.strip()}"
            else:
                return "No identifiable banner received for generic port."

    except socket.timeout:
        return None
    except ConnectionRefusedError:
        return None
    except ssl.SSLError as e:
        return None
    except socket.error as e:
        return None
    except Exception as e:
        return None
    finally:
        if sock:
            sock.close()


def scan_ports_for_banners(target_ip, ports_list):
    results = {}
    logging.info(f"Starting banner scan for {target_ip} on ports: {ports_list}")
    for port in ports_list:
        logging.info(f"Scanning port {port}...")
        banner = get_banner(target_ip, port)
        if banner:
            results[port] = banner
    return str(results)
