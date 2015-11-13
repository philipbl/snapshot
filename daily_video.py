#!/usr/bin/env python3

import video_maker
import glob
import arrow
import re
import configparser
import requests
import yaml
import logging
import logging.config
import snapshot
import os.path
import os
from glob import iglob
from itertools import product
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor


# Log configuration
logging.config.dictConfig(yaml.load(open('logging.yaml')))
logger = logging.getLogger("snapshot." + __name__)


def get_range(start_time, end_time):
    today = arrow.now()
    today = today.replace(hour=end_time.hour,
                          minute=end_time.minute,
                          second=end_time.second,
                          microsecond=end_time.microsecond)

    yesterday = today.replace(days=-1)
    yesterday = yesterday.replace(hour=start_time.hour,
                                  minute=start_time.minute,
                                  second=start_time.second,
                                  microsecond=start_time.microsecond)

    logger.debug("start_time: %s\tend_time: %s", start_time, end_time)
    return yesterday.timestamp, today.timestamp


def get_images(start, stop, directory):
    def filter_images(file_):
        m = re.search(".*-(\\d+)\\.jpg", file_, re.I | re.M)
        return start <= int(m.group(1)) <= stop

    return (file_ for file_ in iglob('{}/*.jpg'.format(directory))
            if filter_images(file_))


def send_email(tos, message, key):
    logger.info("Sending email")

    request_url = 'https://api.mailgun.net/v3/mg.lundrigan.org/messages'
    request = requests.post(request_url, auth=('api', key), data={
        'from': 'Hank Cam <hank_cam@lundrigan.org>',
        'to': ', '.join(tos),
        'subject': 'Hank\'s Sleep Video ({})'.format(arrow.now('US/Mountain').strftime('%m/%d/%Y')),
        'text': message,
        'html': message
    })

    logger.info("Email response:\n%s", request.text)


def parse_time(time_str):
    types = [['h', 'hh'], ['mm'], ['a', 'A']]

    for h, m, a in product(*types):
        time_format = '{}:{} {}'.format(h, m, a)

        try:
            logger.debug("Trying time format: %s", time_format)
            return arrow.get(time_str, time_format)
        except arrow.parser.ParserError:
            logger.debug("Time format did not work.")
            pass

    logger.error("Could not find proper time format!")
    raise arrow.parser.ParserError()


def delete_old(video_path, max_keep):
    videos = [(os.stat(video).st_mtime, video)
              for video in iglob(video_path + '/*.mp4')]
    videos = sorted(videos)

    while len(videos) > max_keep:
        video = videos.pop(0)[1]
        logger.info("Deleting %s", video)
        os.remove(video)


def get_run_time(stop_time):
    now = arrow.now()
    run_again = now.replace(hour=stop_time.hour,
                            minute=stop_time.minute + 5,
                            second=stop_time.second,
                            microsecond=stop_time.microsecond)

    if run_again < now:
        run_again = run_again.replace(days=1)

    return run_again.timestamp - now.timestamp


def read_configuration(config_file):
    return yaml.load(open(config_file))


def run_snapshot(config):
    snapshot.run(**config['camera_settings'])


def run_webserver(config):
    port = config['server_settings']['port']
    path = config['video_settings']['directory']

    reactor.listenTCP(port, Site(File(path)))


def run(config):
    frames_path = config['camera_settings']['directory']

    video_path = config['video_settings']['directory']
    duration = config['video_settings']['duration']
    start_time = parse_time(config['video_settings']['start_time'])
    end_time = parse_time(config['video_settings']['end_time'])
    max_keep = config['video_settings']['max_keep']

    send_list = config['email_settings']['send_list']
    message = config['email_settings']['message']
    key = config['email_settings']['key']

    server_url = config['server_settings']['url']
    server_url = '{}:{}'.format(server_url, config['server_settings']['port'])

    def _run():
        images = get_images(*get_range(start_time, end_time), frames_path)
        link = video_maker.create_video(images, duration, video_path)
        send_email(send_list, message.format(server_url + '/' + os.path.basename(link)), key)

        delete_old(video_path, max_keep)

        next_run = get_run_time(end_time)
        reactor.callLater(next_run, _run)
        logger.info("Running again in %s seconds", next_run)

    next_run = get_run_time(end_time)
    reactor.callLater(next_run, _run)
    logger.info("Running again in %s seconds", next_run)


try:
    raise Exception("test")

    logger.info("Reading configuration")
    config = read_configuration('daily_video.yaml')

    logger.info("Starting web server")
    run_webserver(config)

    logger.info("Starting snapshot")
    run_snapshot(config)

    logger.info("Starting daily video")
    run(config)

    logger.info("Running")
    reactor.run()
except:
    logger.exception("Error occurred when running")
