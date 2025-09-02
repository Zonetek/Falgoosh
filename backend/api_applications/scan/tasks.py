from celery import shared_task

from api_applications.scan.services.scan_service import ScanService


@shared_task(bind=True, max_retries=3)
def run_scan_task(self, scan_id, target_ip):
    ScanService.run_scan(scan_id, target_ip)