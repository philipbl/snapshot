import time
import os
import argparse
from foscam import FoscamCamera

parser = argparse.ArgumentParser(description='Takes a snapshot of your Foscam at every interval.')

parser.add_argument('-l', '--url', required=True,
                   help='The URL for the camera. Do not include protocol (http). ' \
                   'Example: 192.168.0.51:8996')

parser.add_argument('-u', '--user_name', required=True,
                   help='The user name for the camera.')

parser.add_argument('-p', '--password', required=True,
                   help='The password for the camera.')

parser.add_argument('-i', '--interval', required=True, type=int,
                   help='The interval to take snapshots (in seconds).')

args = parser.parse_args()

url = args.url
user_name = args.user_name
password = args.password
interval = args.interval

camera = FoscamCamera(url, user_name, password)

while True:
    try:
        image = camera.snapshot()
    except:
        print "ERROR: Could not connect to camera."
        pass

    now = time.localtime()
    time_str = time.strftime("%Y-%m-%d_%H:%M%:%S", now)
    directory = time.strftime("%Y/%m/%d", now)
    file_name = "{0}/snapshot-{1}.jpg".format(directory, time_str)

    try:
        # Create a folder for images for that day
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_name, 'w') as f:
            f.write(image)

        print "Saved {0}".format(file_name)
    except:
        print "ERROR: Could not save image."
        pass

    time.sleep(interval)
