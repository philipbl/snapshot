#!/usr/bin/env python3
import re
import arrow
import hashlib
import os
import os.path
import tempdir
from subprocess import Popen
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from tempfile import NamedTemporaryFile

ffmpeg_command = "/usr/local/bin/ffmpeg -framerate {} -pattern_type glob -i '{}' -c:v libx264 -r 30 -pix_fmt yuv420p {}/{}"


def _add_timestamp(files, temp_path):
    def get_time(file_name):
        timestamp = re.search("(\\d{10})", file_name).group(1)
        timestamp = arrow.get(timestamp)
        timestamp = timestamp.to('US/Mountain')
        return timestamp.strftime("%I:%M %p")

    font = ImageFont.truetype("SanFranciscoDisplay-Regular.otf", 30)

    # Populate temporary folder
    for i, file_name in enumerate(files):
        img = Image.open(file_name)
        draw = ImageDraw.Draw(img)
        draw.text((10, 440), get_time(file_name), (255,255,255), font=font)

        img.save('{}/{}'.format(temp_path, os.path.basename(file_name)))

    return "{}/*.jpg".format(temp_path)


def _make_video(frames_path, duration, video_path):
    video_name = hashlib.sha256(str(arrow.now()).encode('utf8')).hexdigest() + ".mp4"

    print(ffmpeg_command.format(duration,
                                frames_path,
                                video_path,
                                video_name))

    process = Popen(ffmpeg_command.format(duration,
                                          frames_path,
                                          video_path,
                                          video_name),
                    shell=True)
    process.wait()

    return "{}/{}".format(video_path, video_name)


def create_video(files, duration, video_path):
    with tempdir.TempDir() as t:
        frames_path = _add_timestamp(files, t)
        _make_video(frames_path, duration, video_path)
