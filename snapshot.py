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
import sched
from collections import deque
from docopt import docopt
from foscam import FoscamCamera
from glob import glob

# Add output option to tell which folder to out images to

# def run(url, user_name, password, interval, scheduler, directory='.', max_keep=None):
def run(scheduler, **kwargs):
    try:
        url = kwargs['url']
        user_name = kwargs['user_name']
        password = kwargs['password']
        interval = kwargs.get('interval', 60)
        directory = kwargs.get('directory', '.')
        max_keep = kwargs.get('max_keep')
    except Exception as e:
        print("Error: Must pass {} as a parameter.".format(e))
        exit()

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

    def _run():
        try:
            image = camera.snapshot()
        except Exception as ex:
            print(ex)
            print("ERROR: Could not connect to camera.")
            scheduler.enter(interval, 1, _run)
            return

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
            scheduler.enter(interval, 1, _run)
            return

        scheduler.enter(interval, 1, _run)

    _run()
    scheduler.run()

if __name__ == '__main__':
    args = docopt(__doc__, version='snapshot 1.0')
    print(args)

    run(sched.scheduler(),
        url=args['<url>'],
        user_name=args['<user_name>'],
        password=args['<password>'],
        interval=int(args['<interval>']),
        directory=args['<directory>'] if args['-d'] else '.',
        max_keep=int(args['<max_keep>']) if args['--max'] else None)
