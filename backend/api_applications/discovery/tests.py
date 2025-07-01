import unittest

import port_scanner
import scanner


class test(unittest.TestCase):
    def test_call_ip_range_with_real_yaml(self):

        ip_range = "127.0.0.1/32"
        port_scanner.call_ip_range(ip_range)

    def test_scan_ports(self):

        ip, open_ports = port_scanner.scan_ports("127.0.0.1", [80, 22])
        print(f"IP: {ip}, Open Ports: {open_ports}")
        self.assertEqual(ip, "127.0.0.1")

    def test_generate_public_ipv4_ranges_stream(self):

        gen = scanner.generate_public_ipv4_ranges_stream(8)
        results = [next(gen) for _ in range(5)]
        for subnet in results:
            self.assertIsInstance(subnet, str)
            self.assertIn("/", subnet)


if __name__ == "__main__":
    unittest.main()
