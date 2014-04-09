import time
import os
from foscam import FoscamCamera

url = '192.168.0.98:8110'
user_name = 'test'
password = 'test'
interval = 10

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
