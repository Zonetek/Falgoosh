import unittest
from unittest.mock import MagicMock, patch
import vulnerability
import banner_grabber

class TestBannerGrabber(unittest.TestCase):

    @patch("socket.socket")
    def test_get_banner_ssh_success(self, mock_socket):
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.recv.return_value = (
            b"SSH-2.0-OpenSSH_7.6p1 Ubuntu-4ubuntu0.3\r\n"
        )

        result = banner_grabber.get_banner("192.168.1.1", 22)
        self.assertIn("SSH:", result)
        self.assertIn("SSH-2.0-OpenSSH_7.6p1 Ubuntu-4ubuntu0.3", result)
        mock_sock_instance.connect.assert_called_with(("192.168.1.1", 22))
        mock_sock_instance.recv.assert_called_with(1024)
        mock_sock_instance.close.assert_called_once()

    @patch("socket.socket")
    def test_get_banner_ftp_success(self, mock_socket):
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.recv.return_value = b"220 (vsFTPd 3.0.3)\r\n"

        result = banner_grabber.get_banner("192.168.1.1", 21)
        self.assertIn("FTP:", result)
        self.assertIn("220 (vsFTPd 3.0.3)", result)
        mock_sock_instance.connect.assert_called_with(("192.168.1.1", 21))
        mock_sock_instance.recv.assert_called_with(1024)
        mock_sock_instance.close.assert_called_once()

    @patch("socket.socket")
    def test_get_banner_http_success(self, mock_socket):
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        http_response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Server: Apache/2.4.29 (Ubuntu)\r\n"
            b"Content-Type: text/html\r\n\r\n"
            b"<html><body>Hello</body></html>"
        )
        mock_sock_instance.recv.side_effect = [
            http_response[:50],
            http_response[50:],
            b"",
        ]

        result = banner_grabber.get_banner("192.168.1.1", 80)
        self.assertIn("HTTP:", result)
        self.assertIn("Server: Apache/2.4.29 (Ubuntu)", result)
        self.assertIn("Content-Type: text/html", result)
        mock_sock_instance.connect.assert_called_with(("192.168.1.1", 80))
        mock_sock_instance.sendall.assert_called_once()
        mock_sock_instance.close.assert_called_once()

    @patch("ssl.create_default_context")
    @patch("socket.socket")
    def test_get_banner_https_success(self, mock_socket, mock_ssl_context):
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_wrapped_sock = MagicMock()
        mock_ssl_context.return_value.wrap_socket.return_value = mock_wrapped_sock

        https_response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Server: nginx/1.18.0\r\n"
            b"Content-Type: text/html\r\n\r\n"
            b"<html><body>Secure Hello</body></html>"
        )
        mock_wrapped_sock.recv.side_effect = [
            https_response[:50],
            https_response[50:],
            b"",
        ]

        result = banner_grabber.get_banner("192.168.1.1", 443)
        self.assertIn("HTTPS:", result)
        self.assertIn("Server: nginx/1.18.0", result)
        self.assertIn("Content-Type: text/html", result)
        mock_wrapped_sock.connect.assert_called_with(("192.168.1.1", 443))
        mock_wrapped_sock.sendall.assert_called_once()
        mock_wrapped_sock.close.assert_called_once()

    @patch("socket.socket")
    def test_get_banner_generic_success(self, mock_socket):
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.recv.return_value = b"Some generic service banner\r\n"

        result = banner_grabber.get_banner("192.168.1.1", 12345)
        self.assertIn("Generic/Unknown Service:", result)
        self.assertIn("Some generic service banner", result)
        mock_sock_instance.connect.assert_called_with(("192.168.1.1", 12345))
        mock_sock_instance.recv.assert_called_with(4096)
        mock_sock_instance.close.assert_called_once()

if __name__ == "__main__":
    unittest.main()
