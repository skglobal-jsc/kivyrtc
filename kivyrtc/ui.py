from queue import Queue
import asyncio

from aiortc.mediastreams import MediaStreamError
from kivy.uix.image import Image
from kivy.clock import mainthread
from kivy.graphics.texture import Texture
from kivy.logger import Logger


class MediaRecorderContext:
    def __init__(self, stream, sender):
        self.stream = stream
        self.sender = sender
        self.task = None
        self.queue = Queue()

class MediaStreamer:
    def __init__(self, container, format=None, options={}):
        self.__container = container
        self.__tracks = {}
        self.__lock = asyncio.Lock()

    async def addTrack(self, track, sender):
        """
        Add a track to be recorded.

        """
        async with self.__lock:
            if track.kind == 'video':
                stream = StreamView(
                    pos_hint={'center_x': 0.5, 'center_y': 0.5},
                    size_hint=[1,1],
                )
                self.__container.add_widget(stream)
                self.__tracks[track] = MediaRecorderContext(stream, sender)
            elif track.kind == 'audio':
                self.__tracks[track] = MediaRecorderContext(None, sender)

    async def remove_track(self, sender):
        async with self.__lock:
            items = []
            for track, context in self.__tracks.items():
                if context.sender == sender:
                    context.task.cancel()
                    context.task = None
                    if context.stream is not None:
                        self.__container.remove_widget(context.stream)
                    items.append(track)

            for i in items:
                self.__tracks.pop(i)

    def get_context(self):
        for track, context in self.__tracks.items():
            if track.kind == 'audio':
                yield context

    def start(self):
        """
        Start recording.
        """
        for track, context in self.__tracks.items():
            if context.task is None:
                context.task = asyncio.ensure_future(self.__run_track(track, context))

    async def stop(self):
        """
        Stop recording.
        """
        if self.__container:
            for track, context in self.__tracks.items():
                if context.task is not None:
                    context.task.cancel()
                    context.task = None

                if track.kind == 'video':
                    self.__container.remove_widget(context.stream)
            self.__tracks = {}

    async def __run_track(self, track, context):
        _format = set()
        i = 0
        if track.kind == 'video':
            media_format = 'rgb'
        else:
            media_format = 's16'
        while True:
            try:
                frame = await track.recv()
            except MediaStreamError:
                return

            try:
                if frame.format.name.startswith('yuv'):
                    frame = frame.to_rgb()
                elif frame.format.name != media_format:
                    if frame.format.name not in _format:
                        Logger.warning(f'MediaStreamer: unsupport {track.kind}'
                            f'format {frame.format.name}')
                        _format.add(frame.format.name)
                    return

                media = frame.to_ndarray()
                if track.kind == 'video':
                    context.stream.refresh_widget(media, media_format)
                else:
                    context.queue.put(media)
            except:
                Logger.exception('StreamError:')
                return
            # if i == 0:
            #     print(f"I'm still alive {context.sender}")
            #     print(media.shape)
            #     i = 150
            # else:
            #     i -= 1


class StreamView(Image):
    @mainthread
    def refresh_widget(self, img, format_img):
        if self.texture is None or\
                self.texture.size != [img.shape[1], img.shape[0]]:
            self.allow_stretch = True
            self.texture = Texture.create(size=[img.shape[1], img.shape[0]],
                                            colorfmt=format_img)
            self.texture.flip_vertical()

        self.texture.blit_buffer(img.reshape(-1), colorfmt=format_img)
        self.canvas.ask_update()
