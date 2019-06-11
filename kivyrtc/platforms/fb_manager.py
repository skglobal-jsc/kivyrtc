
from os.path import join

from kivy.utils import platform
from kivy.storage.dictstore import DictStore
from kivy.logger import Logger

if platform == 'android':
    pass
elif platform == 'ios':
    pass
else:
    import webbrowser
    from threading import Thread
    from requests_oauthlib import OAuth2Session
    from requests_oauthlib.compliance_fixes import facebook_compliance_fix
    from flask import Flask
    from flask import request
    import OpenSSL
    import requests

# Credentials you get from registering a new application
client_id = ''
client_secret = ''
client_token = ''

# OAuth endpoints given in the Facebook API documentation
authorization_base_url = \
    ('https://www.facebook.com/v3.2/dialog/oauth')
token_url = \
    'https://graph.facebook.com/oauth/access_token'
refresh_url = \
    ('https://graph.facebook.com/oauth/access_token?'
        'grant_type=fb_exchange_token&'
        'client_id={app_id}&'
        'client_secret={app_secret}&'
        'fb_exchange_token={lived_token}')
get_info_url = \
    ('https://graph.facebook.com/v3.2/me?'
        'fields=first_name,last_name,picture,email&'
        'access_token={token}')
debug_url = \
    ('https://graph.facebook.com/debug_token?'
        'input_token={token_inspect}&'
        'access_token={token}')

host_name = '127.0.0.1'
port = 5000
redirect_uri = 'https://{}:{}/'.format(host_name, port)

class FBManager(object):
    '''
    A Facebook Login for desktop app.

    Note: the redirect link requires https, when opening the web,
    it will say 'Your connection is not private'

    View more on https://developers.facebook.com/docs/facebook-login/manually-build-a-login-flow
    '''
    token = None

    _serv = None
    _list_url = []

    def __init__(self, data_path, refresh_ui):
        self.refresh_ui = refresh_ui
        self.data_path = data_path
        fb_db = DictStore(join(data_path, 'fb.db'))
        if not fb_db.exists('data'):
            fb_db.put('data')
        self.db = fb_db

        if self.db['data'].get('token') and not platform in ('ios', 'android'):
            self.token = self.db['data']['token']
            self.refresh_token()
        else:
            pass

    def get_token(self):
        if not self._serv:
            self._run_server()

        fb = OAuth2Session(client_id, redirect_uri=redirect_uri,
                    scope='email,public_profile')
        self.fb = facebook_compliance_fix(fb)

        # Redirect user to Facebook for authorization
        authorization_url, state = self.fb.authorization_url(authorization_base_url)
        # print(authorization_url)
        webbrowser.open(authorization_url)

    def _run_server(self):
        app = Flask(__name__)

        @app.route("/",methods=['GET', 'POST'])
        def handle_redirect():
            func = request.environ.get('werkzeug.server.shutdown')
            if func is None:
                Logger.warning('Server: Not running with the Werkzeug Server')
            # Get the authorization verifier code from the callback url
            redirect_response = request.url
            if redirect_response in self._list_url:
                return 'This token has been authenticated before.'
            self._list_url.append(redirect_response)
            handle_thr = Thread(target=self._handle_fb,args=(redirect_response, func))
            handle_thr.setDaemon(True)
            handle_thr.start()

            return "All done"

        kw = {
            'ssl_context':'adhoc',
            'host': host_name,
            'port': port
        }
        self._serv = thr = Thread(target=app.run, kwargs=kw)
        thr.setDaemon(True)
        thr.start()

    def _handle_fb(self, value, shutdown_serv):
        # Fetch the access token
        data = self.fb.fetch_token(token_url, client_secret=client_secret,
                                authorization_response=value)
        self.token = data['access_token']
        self.update_info()
        if self.token:
            self.refresh_ui()
        # Logger.info('Server: Shutting down...')
        # shutdown_serv()
        # self.serv.join(timeout=5)

    def update_info(self):
        db = {}
        r = requests.get(debug_url.format(token_inspect=self.token,
                                        token=self.token))
        # if r.status_code == 200:
        #     js = r.json()['data']
        #     db['token'] = self.token
        #     db['user_id'] = js['user_id']
        #     db['scopes'] = js['scopes']
        # Fetch a protected resource, i.e. user profile
        r = requests.get(get_info_url.format(token=self.token))
        if r.status_code == 200:
            js = r.json()
            db['token'] = self.token
            db['user_id'] = js['id']
            db['first_name'] = js['first_name']
            db['last_name'] = js['last_name']
            db['picture'] = js['picture']['data']
            db['email'] = js.get('email', '')
            self.db['data'] = db
            r = requests.get(js['picture']['data']['url'], stream=True)
            if r.status_code == 200:
                with open(join(self.data_path, 'pro_file_pic.jpg'), 'wb') as f:
                    for chunk in r:
                        f.write(chunk)
        else:
            self.token = None
            Logger.warning('Server: Get info {}'.format(r.content))
        # else:
        #     self.token = None
        #     Logger.warning('Server: Check token {}'.format(r.content))

    def refresh_token(self):
        r = requests.get(refresh_url.format(
                                    app_id=client_id,
                                    app_secret=client_secret,
                                    lived_token=self.token))
        if r.status_code == 200:
            js = r.json()
            db = self.db['data']
            db['token'] = self.token = js['access_token']
            self.db['data'] = db
        else:
            self.token = None
            Logger.warning('Server: Refresh token {}'.format(r.content))

    def logout(self):
        self.token = None
        self.db['data'] = {}
        if hasattr(self, 'fb'):
            del self.fb
        self.refresh_ui()

if __name__ == "__main__":
    fbm = FBManager('.', object)
    fbm.get_token()
    from time import sleep
    while not fbm.token:
        sleep(1)
    print(fbm.token)
