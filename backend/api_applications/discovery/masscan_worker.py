import ipaddress
import json
import os
import re
import subprocess


# TODO: using masscan to make the service faster
def masscan_execution(ip, ports="0-1023", rate=50):
    pass


def parse_masscan_output(raw_output):
    pass


def save_result_to_json(new_result, filename="RESULTS_FILE"):
    pass
