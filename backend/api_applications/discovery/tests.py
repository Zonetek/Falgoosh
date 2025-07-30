import unittest
import os 
import sys 
from unittest.mock import patch
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

sys.path.append(current_dir)
sys.path.append(parent_dir)

from discovery import port_scanner
from discovery import scanner
class test(unittest.TestCase):
    def test_call_ip_range_with_real_yaml(self):

        ip_range = "127.0.0.1/32"
        port_scanner.call_ip_range(ip_range)

    @patch("discovery.port_scanner.scan_ports")
    def test_scan_ports(self, mock_scan):
        mock_scan.return_value = ("127.0.0.1", [22, 80])
        ip, open_ports = port_scanner.scan_ports("127.0.0.1")
        self.assertEqual(ip, "127.0.0.1")
        self.assertListEqual(open_ports, [22, 80])

    def test_generate_public_ipv4_ranges_stream(self):

        gen = scanner.generate_public_ipv4_ranges_stream(8)
        results = [next(gen) for _ in range(5)]
        for subnet in results:
            self.assertIsInstance(subnet, str)
            self.assertIn("/", subnet)


if __name__ == "__main__":
    unittest.main()
