from config import *
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint
from scrapli import Scrapli
from scrapli.exceptions import ScrapliConnectionError
from datetime import datetime
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import re
import orionsdk
import copy

HOUR_SECONDS = 3600
DAY_SECONDS = 24 * HOUR_SECONDS
WEEK_SECONDS = 7 * DAY_SECONDS
YEAR_SECONDS = 365 * DAY_SECONDS

device = {
    'host': None,
    'auth_username': username,
    'auth_password': password,
    'auth_strict_key': False,
    'ssh_config_file': '~/.ssh/config',
    'platform': 'cisco_iosxe',
    #'transport': 'paramiko',
    #'port': 22,
}

def get_devices():
    device_list = []
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    npm_client = orionsdk.SwisClient(npm_server, npm_username, npm_password)
    npm_results = npm_client.query(npm_query)['results']
    #import ipdb; ipdb.set_trace()
    for result in npm_results:
        my_device = copy.copy(device)
        my_device.update({'host': result['hostname']})
        device_list.append(my_device)
    return device_list

def parse_uptime(uptime_str):
    """
    Extract the uptime string from the given Cisco IOS Device.
    Return the uptime in seconds as an integer
    """
    # Initialize to zero
    (years, weeks, days, hours, minutes) = (0, 0, 0, 0, 0)

    uptime_str = uptime_str.strip()
    time_list = uptime_str.split(",")
    for element in time_list:
        if re.search("year", element):
            years = int(element.split()[0])
        elif re.search("week", element):
            weeks = int(element.split()[0])
        elif re.search("day", element):
            days = int(element.split()[0])
        elif re.search("hour", element):
            hours = int(element.split()[0])
        elif re.search("minute", element):
            minutes = int(element.split()[0])

    uptime_sec = (
	(years * YEAR_SECONDS)
	+ (weeks * WEEK_SECONDS)
	+ (days * DAY_SECONDS)
	+ (hours * 3600)
	+ (minutes * 60)
    )
    return uptime_sec

def int_time(int_time):
    # https//github.com/napalm-automation/napalm/blob/develop/napalm/ios/ios.py#L1233
    """
    Convert string time to seconds.
    Examples
    00:14:23
    00:13:40
    00:00:21
    00:00:13
    00:00:49
    1d11h
    1d17h
    1w0d
    8w5d
    1y28w
    never
    """
    int_time = int_time.strip()
    uptime_letters = set(["w", "h", "d"])

    if "never" in int_time:
        return -1
    elif ":" in int_time:
        times = int_time.split(":")
        times = [int(x) for x in times]
        hours, minutes, seconds = times
        return (hours * 3600) + (minutes * 60) + seconds
    # Check if any letters 'w', 'h', 'd' are in the time string
    elif uptime_letters & set(int_time):
        form1 = r"(\d+)d(\d+)h"  # 1d17h
        form2 = r"(\d+)w(\d+)d"  # 8w5d
        form3 = r"(\d+)y(\d+)w"  # 1y28w
        match = re.search(form1, int_time)
        if match:
            days = int(match.group(1))
            hours = int(match.group(2))
            return (days * DAY_SECONDS) + (hours * 3600)
        match = re.search(form2, int_time)
        if match:
            weeks = int(match.group(1))
            days = int(match.group(2))
            return (weeks * WEEK_SECONDS) + (days * DAY_SECONDS)
        match = re.search(form3, int_time)
        if match:
            years = int(match.group(1))
            weeks = int(match.group(2))
            return (years * YEAR_SECONDS) + (weeks * WEEK_SECONDS)
    raise ValueError(
        "Unexpected value for interface uptime string: {}".format(int_time)
    )

def is_up(port):
    return 'up' in port['link_status'] and 'up' in port['protocol_status']

def is_down(port):
    return not is_up(port)

def last_output(port):
    last_output = port['last_output']
    if last_output == 'never':
        return None
    else:
        return int_time(last_output)

def last_used(port):
    if is_up(port):
        return 'Now'
    if not last_output(port):
        return 'Never'
    else:
        #last_output_seconds = last_output(port)
        #last_output_timestamp = datetime.now().timestamp() - last_output_seconds
        #return datetime.fromtimestamp(last_output_timestamp)
        return port['last_output']

def never_used(port):
    return is_down(port) and not last_output(port)


def is_unused(port, cutoff=WEEK_SECONDS):
    if never_used(port):
        return True
    else:
        return is_down(port) and last_output(port) >= cutoff

def is_used(port, cutoff=WEEK_SECONDS):
    return not is_unused(port, cutoff)

def get_port_num(port):
    """ Returns port number
        e.g. GigabitEthernet1/0/36 returns 36
    """
    if type(port) is int:
        return port
    else:
        return int(port['interface'].split('/')[-1])

def is_access_port(port):
    return port['media_type'] == '10/100/1000BaseTX'

def find_unused_ports(ports):
    results = []
    for port in ports:
        if is_access_port(port):
            if is_unused(port):
                results.append(port)
    return results

def get_port_status(ports):
    results = []
    for port in ports:
        if is_access_port(port):
            results.append({
                'port': get_port_num(port),
                'is_in_use': is_used(port),
                'last_used': last_used(port)
            })
    return results

def get_unused_ports(device, min_uptime=WEEK_SECONDS):
    unused = []
    port_result = {
        'success': False,
        'host': device['host'],
        'unused_ports': None,
        'msg': '',
    }
    try:
        with Scrapli(**device) as conn:
            response = conn.send_command("show interfaces")
            result = response.textfsm_parse_output()
            response = conn.send_command("sh ver | i uptime")
            hostname, uptime_str = response.result.split(" uptime is ")
            uptime = parse_uptime(uptime_str)
    except ScrapliConnectionError:
        port_result.update({'msg': 'Error connecting to device'})
        return port_result
    if uptime < min_uptime:
        port_result.update({'msg': 'Device does not meet minimum uptime'})
        return port_result
    unused_ports = find_unused_ports(result)
    if len(unused_ports) > 0:
        for port in unused_ports:
            unused.append(get_port_num(port))
        port_result.update({'success': True, 'unused_ports': unused})
    else:
        port_result.update({'msg': 'No available ports found'})
    return port_result

def get_all_unused_ports(devices):
    with ThreadPoolExecutor(max_workers=50) as executor:
        return executor.map(get_unused_ports, devices)

def main():
    devices = get_devices()
    all_unused_ports = get_all_unused_ports(devices)
    for result in all_unused_ports:
        msg = result['unused_ports'] or result['msg']
        print(f"{result['host']}: {msg}")

if __name__ == "__main__":
    main()
