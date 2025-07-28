import unittest
from unittest.mock import patch, MagicMock

import finger_print
import geo_info
import dns_reverse
import db_operations

class TestFingerPrint(unittest.TestCase):
    @patch('finger_print.nmap.PortScanner')
    def test_os_finger_print_with_osclass(self, mock_portscanner):
        mock_scan = MagicMock()
        mock_osclass = {
            "osfamily": "Linux",
            "type": "general purpose",
            "osgen": "5.X",
            "vendor": "Debian"
        }
        mock_scan.__getitem__.return_value = {
            "osmatch": [{
                "name": "Debian Linux 5.x",
                "accuracy": "99",
                "osclass": [mock_osclass]
            }]
        }
        mock_portscanner.return_value = mock_scan
        
        result = finger_print.os_finger_print("127.0.0.1")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["os_match"], "Debian Linux 5.x")
        self.assertEqual(result["os_family"], "Linux")
        self.assertEqual(result["accuracy"], "99")
        self.assertEqual(result["type"], "general purpose")
        self.assertEqual(result["os_Gen"], "5.X")
        self.assertEqual(result["vendor"], "Debian")

    @patch('finger_print.nmap.PortScanner')
    def test_os_finger_print_without_osclass(self, mock_portscanner):
        mock_scan = MagicMock()
        mock_scan.__getitem__.return_value = {
            "osmatch": [{
                "name": "Unknown OS",
                "accuracy": "60"
            }]
        }
        mock_portscanner.return_value = mock_scan
        
        result = finger_print.os_finger_print("127.0.0.1")
        self.assertIn("os_match", result)
        self.assertIn("accuracy", result)

class TestGeoInfo(unittest.TestCase):
    @patch('geo_info.requests.get')
    def test_geo_info(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "country": "United States",
            "city": "Mountain View",
            "regionName": "California",
            "lat": 37.386,
            "lon": -122.0838,
            "isp": "Google LLC",
            "org": "Google",
            "as": "AS15169"
        }
        mock_get.return_value = mock_response

        result = geo_info.geo_info("8.8.8.8")
        self.assertIn("geo", result)
        self.assertEqual(result["geo"]["country"], "United States")
        self.assertEqual(result["geo"]["city"], "Mountain View")
        self.assertEqual(result["geo"]["regionname"], "California")
        self.assertEqual(result["geo"]["latlang"], [37.386, -122.0838])
        self.assertEqual(result["isp"], "Google LLC")
        self.assertEqual(result["organization"], "Google")
        self.assertEqual(result["asn"], "AS15169")

class TestDNSReverse(unittest.TestCase):
    @patch('dns_reverse.socket.gethostbyaddr')
    def test_get_domain_success(self, mock_gethostbyaddr):
        mock_gethostbyaddr.return_value = ("example.com", [], [])
        domain = dns_reverse.get_domain("8.8.8.8")
        self.assertEqual(domain, "example.com")

    @patch('dns_reverse.socket.gethostbyaddr')
    def test_get_domain_failure(self, mock_gethostbyaddr):
        mock_gethostbyaddr.side_effect = dns_reverse.socket.herror
        domain = dns_reverse.get_domain("255.255.255.255")
        self.assertIsNone(domain)

class TestDBOperations(unittest.TestCase):
    @patch('db_operations.monogo_connections.connect_monogo')
    @patch('db_operations.finger_print.os_finger_print')
    @patch('db_operations.geo_info.geo_info')
    @patch('db_operations.dns_reverse.get_domain')
    def test_update_enrichment(
        self, mock_get_domain, mock_geo_info, mock_fp, mock_connect_monogo
    ):
        mock_db = MagicMock()
        mock_coll = MagicMock()
        mock_db.scan_results = mock_coll
        mock_connect_monogo.return_value = mock_db
        mock_coll.find.return_value = [
            {
                "_id": "1.2.3.4",
                "ports": [22, 80]
            }
        ]
        mock_fp.return_value = {"os_match": "Test OS"}
        mock_geo_info.return_value = {"geo": {"country": "Testland"}}
        mock_get_domain.return_value = "test.domain"

        db_operations.update_enrichment()
        mock_coll.update_one.assert_called_with(
            {"_id": "1.2.3.4"},
            {"$set": {
                "finger_print": {"os_match": "Test OS"},
                "general": {"geo": {"country": "Testland"}},
                "domain": "test.domain"
            }}
        )

if __name__ == '__main__':
    unittest.main()
