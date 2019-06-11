
from os.path import abspath, dirname, join
from kivy.lang import Builder

Builder.load_file(abspath(
            join(dirname(__file__), 'fb_widget.kv')))

class ImageButton: pass

class AccountWidget: pass
