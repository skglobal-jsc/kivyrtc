import webbrowser
from os.path import join, abspath, dirname

import requests
from kivy.logger import Logger
from kivy.lang import Builder
from kivy.utils import get_color_from_hex as to_color
from kivy.properties import ListProperty, StringProperty, BooleanProperty
from kivy.clock import Clock , ClockBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

if __name__ == '__main__':
    IS_RELEASE = False
    PLATFORM = 'win'
else:
    from __main__ import IS_RELEASE, PLATFORM

Builder.load_file(abspath(
            join(dirname(__file__), 'get_ads.kv')))

whoami_url = 'http://srv.buysellads.com/ads/whoami'
whoami_r = r'^You are (\d+) \((\d+), (\d+); (\d+) / (\d+) / (\d+) / (\d+) / (\d+); (\d+)'
#You are USERID (IP_ADDRESS, USER_AGENT; COUNTRY / BROWSER / OS / REGION / CITY)
buysellads_url = 'http://srv.buysellads.com/ads/{}.json'

if IS_RELEASE:
    ZONEKEY = ''
else:
    ZONEKEY = 'CKYD623L'

def get_ads_buysellads(zonekey=None, segment='', forcenads=1):
    '''
    Get ads from buysellads

    View more on http://customads.bsademo.com/reference/api.html
    '''
    params = {
        'ignore': 'no' if IS_RELEASE else 'yes', # Whether or not to track this impression
        'track': 'no' if IS_RELEASE else 'yes', # Specify to NOT track via the bsawt cookie
        'segment': segment,
        'forcenads': forcenads, # Request a number of ads to be returned
        # 'freqcap': '', # Frequency capping data
        # 'callback': '', # Only response type: .js
        # 'forwardedip': '',
        # 'browser': '',
        # 'os': '',
        # 'country': '',
        # 'useragent': '',
        # 'ignorebanner': '', # ID (admanbanner) to never serve
        # 'maxpriority': '', # Max priority level to serve
    }
    r = requests.get(buysellads_url.format(zonekey if zonekey else ZONEKEY),
                        params=params)
    if r.status_code != 200:
        text = '\n'+r.text if r.text else ''
        Logger.warning('Ads buysellads: request fail'+text)

    for i in r.json()['ads']:
        # If no "statlink" parameter exists within the response,
        # then there are no ads to serve for the current request.
        if not i.get('statlink'):
            text = '\n'+r.text if r.text else ''
            Logger.warning('Ads buysellads: have no statlink'+text)
            continue

        if i['rendering'] not in ('default', 'fancybar', 'flexbar'):
            text = '\n'+r.text if r.text else ''
            Logger.warning('Ads buysellads: unknown type'+text)
            continue

        yield {
            'icon': i['image'],
            'bg_color': to_color(i['backgroundColor']),
            'bg_color_hover': to_color(i['backgroundHoverColor']),
            'logo': i['logo'],
            'title': i['title'],
            'description': i['description'],
            'text_color': to_color(i['textColor']),
            'text_color_hover': to_color(i['textColorHover']),
            'button_text': i['callToAction'].upper(),
            'button_color': to_color(i['ctaBackgroundColor']),
            'button_color_hover': to_color(i['ctaBackgroundHoverColor']),
            'button_text_color': to_color(i['ctaTextColor']),
            'button_text_color_hover': to_color(i['ctaTextColorHover']),
            'go_link': 'https:'+i['statlink'],
        }

class AdsBase(Widget):
    icon = StringProperty()
    logo = StringProperty()
    bg_color = ListProperty([0,0,0,0])
    bg_color_hover = ListProperty([0,0,0,0])

    title = StringProperty()
    description = StringProperty()
    text_color = ListProperty([1,1,1])
    text_color_hover = ListProperty([0,0,0,0])

    go_link = StringProperty(None)

    button_text = StringProperty()
    button_color = ListProperty([0,0,0,0])
    button_color_hover = ListProperty([0,0,0,0])
    button_text_color = ListProperty([0,0,0,0])
    button_text_color_hover = ListProperty([0,0,0,0])

    def __init__(self, **kw):
        super(AdsBase, self).__init__(**kw)
        self.update_content()
        self._ads_update = Clock.schedule_interval(self.update_content, 10)

    def update_content(self, *arg):
        for i in get_ads_buysellads():
            for j, data in i.items():
                setattr(self, j, data)
            return

        if not self.parent:
            self._ads_update.cancel()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            return True

    def on_touch_up(self, touch):
        if touch.grab_current is self and self.collide_point(*touch.pos):
            touch.ungrab(self)
            if PLATFORM == 'android':
                from jnius import autoclass, cast
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')

                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                open_action = Intent(Intent.ACTION_VIEW)
                open_action.setData(Uri.parse(self.go_link))
                activity.startActivity(open_action)
            else:
                webbrowser.open(self.go_link)
            return True

class BannerAds(AdsBase, BoxLayout):
    '''
    View more on http://customads.bsademo.com/reference/stickybox.html
    '''
    dark_theme = BooleanProperty(False)
    radius = ListProperty([0,0,0,0])

class FullBannerAds(AdsBase, BoxLayout):
    '''
    View more on http://customads.bsademo.com/reference/flexbar.html
    '''
    pass


if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.floatlayout import FloatLayout

    class MainApp(App):
        def build(self):
            root = FloatLayout()
            root.add_widget(BannerAds(pos_hint={'top': 1, 'center_x': .5}))
            root.add_widget(FullBannerAds(pos_hint={'y': 0, 'center_x': .5}))

            return root

    MainApp().run()
