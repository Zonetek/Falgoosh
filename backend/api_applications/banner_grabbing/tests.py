import socket
import ssl
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

class TestVulnerabilityModule(unittest.TestCase):

    def test_get_service_ssh(self):
        banners = {
            22: "SSH-2.0-OpenSSH_7.6p1 Ubuntu-4ubuntu0.3"
        }
        result = vulnerability.get_service(banners)
        self.assertTrue(any("OpenSSH" in x for x in [r[0] for r in result]))

    def test_get_service_ftp(self):
        banners = {
            21: "220 vsFTPd 3.0.3"
        }
        result = vulnerability.get_service(banners)
        self.assertTrue(any("vsFTPd" in x for x in [r[0] for r in result]))

    def test_get_service_http_server(self):
        banners = {
            80: "HTTP/1.1 200 OK Server: Apache/2.4.29 (Ubuntu) X-Powered-By: PHP/7.2.24"
        }
        result = vulnerability.get_service(banners)
        found_services = [s[0] for s in result]
        self.assertIn("Apache", found_services)
        self.assertIn("PHP", found_services)

    def test_get_service_no_match(self):
        banners = {8080: "Nothing to match here"}
        result = vulnerability.get_service(banners)
        self.assertEqual(result, [(None, None)])

    @patch("gzip.open")
    @patch("os.path.join")
    def test_search_cve_by_service_version_returns_results(self, mock_join, mock_gzip_open):
        mock_join.return_value = "fakepath"
        fake_cve_data = {
            "CVE_Items": [
                {
                    "cve": {
                        "CVE_data_meta": {"ID": "CVE-2021-0001", "ASSIGNER": "testassigner"},
                        "description": {"description_data": [
                            {"value": "apache 2.4.29 remote vulnerability"}
                        ]}
                    },
                    "publishedDate": "2021-01-01T00:00Z"
                }
            ]
        }
        mock_gzip_open.return_value.__enter__.return_value = MagicMock()
        with patch("json.load", return_value=fake_cve_data):
            result = vulnerability.search_cve_by_service_version(("Apache", "2.4.29"))
        self.assertTrue(any("CVE-2021-0001" in c["cve_id"] for c in result))

    @patch("vulnerability.get_service")
    @patch("vulnerability.search_cve_by_service_version")
    def test_get_vul_with_service(self, mock_search_cve, mock_get_service):
        mock_get_service.return_value = [("Apache", "2.4.29")]
        mock_search_cve.return_value = [
            {"cve_id": "CVE-2020-1234", "description": "Fake vul", "published": "2020-12-01"}
        ]
        banners = {80: "Server: Apache/2.4.29"}
        vulns = vulnerability.get_vul(banners)
        self.assertIn("Apache", vulns)
        self.assertEqual(vulns["Apache"][0]["cve_id"], "CVE-2020-1234")

    def test_get_service_multiple_banners(self):
        banners = {
            21: "220 vsFTPd 3.0.3",
            25: "220 mail.example.com ESMTP Postfix",
            80: "HTTP/1.1 200 OK Server: Nginx/1.18.0"
        }
        result = vulnerability.get_service(banners)
        all_services = [svc[0] for svc in result]
        self.assertTrue(any(s in all_services for s in ["vsFTPd", "Postfix", "Nginx"]))
    

if __name__ == "__main__":
    unittest.main()
