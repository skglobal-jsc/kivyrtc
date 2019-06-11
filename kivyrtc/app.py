from os.path import join, abspath, dirname
import threading
import asyncio

import numpy as np
import cv2
from sounddevice import OutputStream
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
)
from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.resources import resource_add_path

from utils.platform import IS_RELEASE, PLATFORM, IS_BINARY
from .janus import JanusPlugin, JanusSession, JANUS_URL
from .mediastreams import VideoImageTrack, AudioTrack
from .ui import MediaStreamer

resource_add_path(
    abspath(join(dirname(__file__), 'data')))


class KivyRTCApp(App):
    """
    A simple RTC client for Kivy use aiortc
    """
    _thread = None
    _update_cam = None
    _device = None
    _device_info = [0, 1920, 1080]
    is_running = False

    def __init__(self, app_name, user_data_dir, **kwargs):
        super(KivyRTCApp, self).__init__(**kwargs)

        self._app_name = app_name
        self._user_data_dir = user_data_dir
        self.title = app_name
        self.icon = Config.get('kivy', 'window_icon')

    def build(self):
        root = Builder.load_file('kivyrtc/main-layout.kv')

        return root

    def on_start(self):
        # Display FPS of app
        # from .tools.show_fps import ShowFPS
        # ShowFPS(self.root)

        for i in range(10):
            try:
                self._create_camera(i)
                status, _ = self._device.read()
                if status:
                    self._device_info[0] = i
                    break
            except:
                pass
        else:
            raise RuntimeError("Can't start camera")

        self.root.ids.room.text = '1234567'
        self.root.ids.server.text = JANUS_URL
        self._update_cam = Clock.schedule_interval(self._update, 1.0 / 30)

    def on_stop(self):
        if self._thread and self._thread.is_alive():
            self.leave_room()
            self._thread.join()

        if self._update_cam is not None:
            self._update_cam.cancel()
            self._update_cam = None

        self._device.release()

    def _create_camera(self, id):
        self._device = cv2.VideoCapture(id)
        self._device.set(cv2.CAP_PROP_FRAME_WIDTH, self._device_info[1])
        self._device.set(cv2.CAP_PROP_FRAME_HEIGHT, self._device_info[2])

    def _update(self, dt):
        if self._device is None:
            self._create_camera(self._device_info[0])

        _, img = self._device.read()
        self.np_img = img

        img_wg = self.root.ids.user_camera
        img_wg.refresh_widget(img, 'bgr')

    def connect_room(self, room):
        if self._thread and self._thread.is_alive(): return

        self.is_running = True
        self._thread = threading.Thread(target=self.run_server, args=[room])
        self._thread.start()

    def leave_room(self):
        if not self._thread: return

        self.is_running = False
        asyncio.run(self.session._queue.put(None))

    def run_server(self, room):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        url = self.root.ids.server.text
        # create signaling and peer connection
        self.session = JanusSession(url)
        self.pc = RTCPeerConnection()
        self.pcs = {}

        # create media source
        video = VideoImageTrack(self)

        audio = AudioTrack(loop)

        # create media sink
        self.recorder = MediaStreamer(self.root.ids.network_camera)

        def out_cb(outdata: np.ndarray, frame_count, time_info, status):
            q_out = None
            for context in self.recorder.get_context():
                try:
                    if q_out is None:
                        q_out = context.queue.get_nowait()
                    else:
                        q_out |= context.queue.get_nowait()
                except:
                    pass

            if q_out is None:
                return

            if q_out.shape == outdata.shape:
                outdata[:] = q_out
            elif q_out.shape[0]*q_out.shape[1] == outdata.shape[0]*outdata.shape[1]:
                outdata[:] = q_out.reshape(outdata.shape)
            else:
                outdata[:] = np.zeros(outdata.shape, dtype=outdata.dtype)
                Logger.warning(f'Audio: wrong size, got {q_out.shape}, should {outdata.shape}')

        # run event loop
        try:
            out_stream = OutputStream(
                blocksize=1920,
                callback=out_cb,
                dtype='int16',
                channels=1,
            )

            with out_stream, audio:
                loop.run_until_complete(
                    self.__run(
                        room=int(room),
                        video=video,
                        audio=audio,
                        )
                )
        finally:
            # cleanup
            loop.run_until_complete(self.recorder.stop())
            loop.run_until_complete(self.pc.close())
            loop.run_until_complete(self.session.destroy())
            for i in self.pcs:
                loop.run_until_complete(self.pcs[i].close())
            self.pcs = {}

            pending = asyncio.Task.all_tasks(loop)
            for task in pending:
                task.cancel()
            # loop.run_until_complete(asyncio.gather(*pending, loop=loop))
            loop.close()

            Logger.info('Loop: closed all')

        self._thread = None

    async def __run(self, room, video, audio):
        await self.session.create()

        # configure media
        media = {
            # "audio": True,
            "video": True,
            "videocodec": "vp8",
            'audiocodec': 'opus',
        }

        self.pc.addTrack(video)
        self.pc.addTrack(audio)

        try:
            self.plugin = await self.session.attach("janus.plugin.videoroom")

            await self.create_roon(room)

            # join video room
            response = await self.plugin.send(
                {
                    "body": {
                        "display": "aiortc",
                        "ptype": "publisher",
                        "request": "join",
                        "room": room,
                    }
                }
            )
            publishers = response['plugindata']['data']['publishers']

            # send offer
            await self.pc.setLocalDescription(await self.pc.createOffer())
            request = {"request": "publish"}
            request.update(media)
            response = await self.plugin.send(
                {
                    "body": request,
                    "jsep": {
                        "sdp": self.pc.localDescription.sdp,
                        "trickle": False,
                        "type": self.pc.localDescription.type,
                    },
                }
            )

            # apply answer
            answer = RTCSessionDescription(
                sdp=response["jsep"]["sdp"], type=response["jsep"]["type"]
            )
            await self.pc.setRemoteDescription(answer)

            if publishers != []:
                for i in publishers:
                    await self.subscribe(i["id"], room)
        except Exception:
            Logger.exception('Join room: fail')
            return

        Logger.info('AppRTC: Start call')
        i = 0
        while True:
            res = await self.session._queue.get()

            if not res:
                if not self.is_running:
                    break
                else:
                    continue

            if res.get('plugindata'):
                await self.new_connect(res, room)

            elif res['janus'] == 'hangup':
                await self.pcs.pop(res['sender']).close()
                self.recorder.remove_track(res['sender'])
                Logger.info(f'AppRTC: {res["sender"]} leave room')

            elif res['janus'] == 'slowlink':
                Logger.info(f"AppRTC: slowlink {res['uplink']} "
                    f"{res['nacks']}")
                tar_plugin = self.session._plugins.get(res["sender"])
                if res['uplink']:
                    await tar_plugin.send({
                        "body": {
                            "request" : "configure",
                            "bitrate" : 64000
                            },
                    })
                else:
                    await tar_plugin.send({
                        "body": {
                            "request" : "configure",
                            "bitrate" : 128000
                            },
                    })

            elif res['janus'] == 'webrtcup':
                if res['sender'] == self.plugin.plugin_id:
                    Logger.info('AppRTC: You are streaming')
                elif res['sender'] in list(self.pcs.keys()):
                    Logger.info(f'AppRTC: You are receiving from {res["sender"]}')
                else:
                    Logger.info(f'AppRTC: Receiving from {res["sender"]} '
                        f'list {list(self.pcs.keys())}')
            elif res['janus'] == 'media':
                if res['sender'] == self.plugin.plugin_id:
                    if res['receiving']:
                        Logger.info(f'AppRTC: {res["type"]} is OK')
                    else:
                        Logger.warning(f'AppRTC: {res["type"]} fail')
            elif res['janus'] == 'keepalive':
                pass
            else:
                print('-'*40)
                for i,j in res.items():
                    print(i,j)
                print('-'*40)

        Logger.info('AppRTC: Leave call')

    async def subscribe(self, sub_id, room):
        plugin = await self.session.attach("janus.plugin.videoroom")
        pc = RTCPeerConnection()
        self.pcs[plugin.plugin_id] = pc

        @pc.on("track")
        async def on_track(track):
            self.recorder.addTrack(track, plugin.plugin_id)

        request = {
            "request" : "join",
            "ptype" : "subscriber",
            "room" : room,
            "feed" : sub_id,
            # "private_id" : ''
        }
        response = await plugin.send(
            {
                "body": request,
            }
        )
        if response['plugindata']['data'].get("error"):
            return
        await pc.setRemoteDescription(RTCSessionDescription(
            sdp=response["jsep"]["sdp"], type=response["jsep"]["type"]
        ))

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        response = await plugin.send(
            {
                "body": {"request" : "start"},
                "jsep": {
                    "sdp": pc.localDescription.sdp,
                    "trickle": False,
                    "type": pc.localDescription.type,
                }
            }
        )
        # print(response)
        self.recorder.start()

    async def new_connect(self, data, room):
        if data['plugindata']['plugin'] == 'janus.plugin.videoroom' and\
                data['plugindata']['data'].get('publishers'):
            publishers = data['plugindata']['data']['publishers']
            for i in publishers:
                await self.subscribe(i["id"], room)

    async def create_roon(self, room):
        res = await self.plugin.send({'body': {
            "request" : "exists",
            "room" : room
        }})
        if res['plugindata']['data']["exists"]:
            return
        params = {
            "request" : "create",
            "room" : room,
            #<unique numeric ID, optional, chosen by plugin if missing>
            "permanent": False,
            #<true|false, whether the room should be saved in the config file, default=false>
            "description": "",
            # This is my awesome room
            'is_private' : False,
            # true|false (private rooms don't appear when you do a 'list' request)
            # 'secret' : '',
            # <optional password needed for manipulating (e.g. destroying) the room>
            # 'pin' : '',
            # <optional password needed for joining the room>
            # 'require_pvtid' : True,
            # true|false (whether subscriptions are required to provide a valid
            #  a valid private_id to associate with a publisher, default=false)
            'publishers' : 5,
            # <max number of concurrent senders> (e.g., 6 for a video
            #  conference or 1 for a webinar, default=3)
            # 'bitrate' : '',
            # <max video bitrate for senders> (e.g., 128000)
            # 'fir_freq' : '',
            # <send a FIR to publishers every fir_freq seconds> (0=disable)
            'audiocodec' : 'opus',
            # opus|g722|pcmu|pcma|isac32|isac16 (audio codec to force on publishers, default=opus
            # can be a comma separated list in order of preference, e.g., opus,pcmu)
            'videocodec' : 'vp8',
            # vp8|vp9|h264 (video codec to force on publishers, default=vp8
            # can be a comma separated list in order of preference, e.g., vp9,vp8,h264)
            # 'opus_fec' : True,
            # true|false (whether inband FEC must be negotiated; only works for Opus, default=false)
            # 'video_svc' : True,
            # true|false (whether SVC support must be enabled; only works for VP9, default=false)
            # 'audiolevel_ext' : False,
            # true|false (whether the ssrc-audio-level RTP extension must be
            # negotiated/used or not for new publishers, default=true)
            # 'audiolevel_event' : True,
            # true|false (whether to emit event to other users or not)
            # 'audio_active_packets' : '' ,
            # 100 (number of packets with audio level, default=100, 2 seconds)
            # 'audio_level_average' : '' ,
            # 25 (average value of audio level, 127=muted, 0='too loud', default=25)
            # 'videoorient_ext' : False,
            # true|false (whether the video-orientation RTP extension must be
            # negotiated/used or not for new publishers, default=true)
            # 'playoutdelay_ext' : False,
            # true|false (whether the playout-delay RTP extension must be
            # negotiated/used or not for new publishers, default=true)
            # 'transport_wide_cc_ext' : True,
            # true|false (whether the transport wide CC RTP extension must be
            # negotiated/used or not for new publishers, default=false)
            # 'record' : True,
            # true|false (whether this room should be recorded, default=false)
            # 'rec_dir' : '' ,
            # <folder where recordings should be stored, when enabled>
            # 'notify_joining' : True,
            # true|false (optional, whether to notify all participants when a new
            # participant joins the room. The Videoroom plugin by design only notifies
            # new feeds (publishers), and enabling this may result extra notification
            # traffic. This flag is particularly useful when enabled with \c require_pvtid
            # for admin to manage listening only participants. default=false)
        }

        await self.plugin.send({"body": params,})
