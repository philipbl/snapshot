#!/usr/bin/env python3
"""
Pulls a snapshot from a foscam camera on a certain interval

Usage:
    snapshot.py <url> <user_name> <password> <interval> [-d <directory>] [--max <max_keep>]
    snapshot.py -h | --help
    snapshot.py -v | --version

Options:
    -h --help       Show this screen.
    -v --version    Show version.
    <url>           The url of the camera (including port number)
    <user_name>     The username to log into the camera
    <password>      The password to log into the camera
    <interval>      How often to take a snapshot (in seconds) [default: 60]
"""

import time
import os
import arrow
from collections import deque
from docopt import docopt
from foscam import FoscamCamera
from glob import glob

# Add output option to tell which folder to out images to

def snapshot(url, user_name, password, interval, directory='.', max_keep=None):
    camera = FoscamCamera(url, user_name, password)

    # Create a folder if necessary
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Keep track of already existing snapshots in that folder
    snaps = deque(glob('{}/snapshot-*.jpg'.format(directory)))

    # Try to delete image if we are above the max
    while max_keep is not None and len(snaps) > max_keep:
        to_delete = snaps.popleft()
        os.remove(to_delete)

    try:
        while True:
            try:
                image = camera.snapshot()
            except Exception as ex:
                print(ex)
                print("ERROR: Could not connect to camera.")
                pass

            now = arrow.now()
            file_name = "{0}/snapshot-{1}.jpg".format(directory, now.timestamp)

            try:
                with open(file_name, 'wb') as f:
                    f.write(image)
                print("Saved {0}".format(file_name))

                # Add it to previous snaps
                snaps.append(file_name)

                # Try to delete image if we are above the max
                while max_keep is not None and len(snaps) > max_keep:
                    to_delete = snaps.popleft()
                    os.remove(to_delete)

            except Exception as ex:
                print(ex)
                print("ERROR: Could not save image.")
                pass

            time.sleep(interval)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    args = docopt(__doc__, version='snapshot 1.0')
    print(args)

    snapshot(args['<url>'],
             args['<user_name>'],
             args['<password>'],
             int(args['<interval>']),
             args['<directory>'] if args['-d'] else '.',
             int(args['<max_keep>']) if args['--max'] else None)
