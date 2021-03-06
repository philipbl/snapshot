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

import arrow
import logging
import os
import time
from collections import deque
from docopt import docopt
from foscam import FoscamCamera
from glob import glob
from twisted.internet import task
from twisted.internet import reactor

logger = logging.getLogger("snapshot." + __name__)

def run(**kwargs):
    try:
        url = kwargs['url']
        user_name = kwargs['user_name']
        password = kwargs['password']
        interval = kwargs.get('interval', 60)
        directory = kwargs.get('directory', '.')
        max_keep = kwargs.get('max_keep')
    except Exception as e:
        logger.error("Error: Must pass {} as a parameter.".format(e))
        print("Error: Must pass {} as a parameter.".format(e))
        exit()

    camera = FoscamCamera(url, user_name, password)

    # Create a folder if necessary
    if not os.path.exists(directory):
        logger.debug("Creating directory %s", directory)
        os.makedirs(directory)

    # Keep track of already existing snapshots in that folder
    snaps = deque(glob('{}/snapshot-*.jpg'.format(directory)))

    # Try to delete image if we are above the max
    while max_keep is not None and len(snaps) > max_keep:
        to_delete = snaps.popleft()
        os.remove(to_delete)
        logger.debug("Deleted %s", to_delete)

    def snapshot():
        try:
            image = camera.snapshot()
        except Exception as ex:
            print("ERROR: Could not connect to camera.")
            logger.error("ERROR: Could not connect to camera. %s", ex)
            return

        now = arrow.now()
        file_name = "{0}/snapshot-{1}.jpg".format(directory, now.timestamp)
        logger.debug("File name: %s", file_name)

        try:
            with open(file_name, 'wb') as f:
                f.write(image)
            logger.info("Saved %s", file_name)

            # Add it to previous snaps
            snaps.append(file_name)

            # Try to delete image if we are above the max
            while max_keep is not None and len(snaps) > max_keep:
                to_delete = snaps.popleft()
                os.remove(to_delete)
                logger.debug("Deleted %s", to_delete)

        except Exception as ex:
            print("ERROR: Could not save image.")
            logger.error("ERROR: Could not connect to camera. %s", ex)
            return

        logger.debug("Scheduling again for %s seconds", interval)

    t = task.LoopingCall(snapshot)
    t.start(interval)


if __name__ == '__main__':
    args = docopt(__doc__, version='snapshot 1.0')
    logger.debug(args)

    run(url=args['<url>'],
        user_name=args['<user_name>'],
        password=args['<password>'],
        interval=int(args['<interval>']),
        directory=args['<directory>'] if args['-d'] else '.',
        max_keep=int(args['<max_keep>']) if args['--max'] else None)

    reactor.run()


