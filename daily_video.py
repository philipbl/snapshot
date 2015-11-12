#!/usr/bin/env python3

import video_maker
import glob
import arrow
import re
import configparser
import requests
import sched
import yaml
import logging
import logging.config
import snapshot
from glob import iglob
from itertools import product


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

    return yesterday.timestamp, today.timestamp


def get_images(start, stop, directory):
    def filter_images(file_):
        m = re.search(".*-(\\d+)\\.jpg", file_, re.I | re.M)
        return start <= int(m.group(1)) <= stop

    return (file_ for file_ in iglob('{}/*.jpg'.format(directory))
            if filter_images(file_))


def send_email(tos, message, key):
    request_url = 'https://api.mailgun.net/v3/mg.lundrigan.org/messages'
    request = requests.post(request_url, auth=('api', key), data={
        'from': 'Hank Cam <alerts@lundrigan.org>',
        'to': ', '.join(tos),
        'subject': 'Hank\'s Sleep Video ({})'.format(arrow.now('US/Mountain').strftime('%m/%d/%Y')),
        'text': message,
        'html': message
    })
    print(request.text)


def parse_time(time_str):
    types = [['h', 'hh'], ['mm'], ['a', 'A']]

    for h, m, a in product(*types):
        time_format = '{}:{} {}'.format(h, m, a)

        try:
            return arrow.get(time_str, time_format)
        except arrow.parser.ParserError:
            pass

    raise arrow.parser.ParserError()


def get_run_time(time):
    run_again = arrow.now().replace(days=1,
                                    hour=end_time.hour,
                                    minute=end_time.minute + 5,
                                    second=end_time.second,
                                    microsecond=end_time.microsecond)

    return run_again.timestamp


def read_configuration(config_file):
    return yaml.load(open(config_file))


def run_snapshot(config, scheduler):
    snapshot.run(scheduler, **config['camera_settings'])


def run(config, scheduler):
    frames_path = config['file_paths']['frames_path']
    video_path = config['file_paths']['video_out_path']

    duration = config['video_settings']['duration']
    start_time = parse_time(config['video_settings']['start_time'])
    end_time = parse_time(config['video_settings']['end_time'])

    send_list = config['email_settings']['send_list']
    message = config['email_settings']['message']
    key = config['email_settings']['key']

    url = config['camera_settings']['url']

    def _run():
        images = get_images(*get_range(start_time, end_time), frames_path)
        link = video_maker.create_video(images, duration, video_path)
        send_email(send_list, message.format(url + '/' + link), key)

        scheduler.enterabs(get_run_time(end_time), 1, _run)

    scheduler.enterabs(get_run_time(end_time), 1, _run,)


config = read_configuration('daily_video.yaml')
scheduler = sched.scheduler(timefunc=lambda : arrow.now().timestamp)

run_snapshot(config, scheduler)
run(config, scheduler)

scheduler.run()
