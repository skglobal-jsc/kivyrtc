import fractions
import time
import logging

from kivy.logger import Logger
from asyncio import Queue
from sounddevice import InputStream
from av import VideoFrame, AudioFrame
from aiortc import (
    VideoStreamTrack,
    AudioStreamTrack,
)
from aiortc.mediastreams import MediaStreamError


class VideoImageTrack(VideoStreamTrack):

    def __init__(self, app):
        super().__init__()  # don't forget this!

        self.app = app

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        # Read camera
        try:
            frame = VideoFrame.from_ndarray(self.app.np_img, format="bgr24")
            frame.pts = pts
            frame.time_base = time_base

            return frame
        except:
            logging.exception('OpenCV: Couldn\'t get image from Camera')

class AudioTrack(AudioStreamTrack):

    def __init__(self, loop):
        super().__init__()

        self.__in_stream = InputStream(
            blocksize=1920,
            callback=self.__callback,
            dtype='int16',
            channels=1,
        )
        self.__queue = Queue()
        self.loop = loop

    def __callback(self, indata, frame_count, time_info, status):
        self.__queue.put_nowait([indata.copy(), status])

    async def recv(self):
        if self.readyState != "live":
            raise MediaStreamError

        data = await self.__queue.get()
        if not data:
            self.stop()
            raise MediaStreamError

        try:
            indata, _ = data
            frame = AudioFrame.from_ndarray(
                indata.reshape(indata.shape[::-1]),
                format='s16',
                layout='mono'
            )

            sample_rate = indata.shape[0]

            if hasattr(self, "_timestamp"):
                samples = int((time.time()-self._start) * sample_rate)
                self._timestamp += samples
            else:
                self._start = time.time()
                self._timestamp = 0

            frame.pts = self._timestamp
            frame.sample_rate = sample_rate
            frame.time_base = fractions.Fraction(1, sample_rate)
            return frame
        except:
            Logger.exception('Audio:')

            self.stop()
            raise MediaStreamError

    def __enter__(self):
        return self.__in_stream.__enter__()

    def __exit__(self, type, value, traceback):
        self.__queue.put_nowait(None)
        self.__in_stream.__exit__(type, value, traceback)
