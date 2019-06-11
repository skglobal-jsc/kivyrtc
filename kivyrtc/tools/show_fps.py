from kivy.lang import Builder
from kivy.app import App
from kivy.uix.stacklayout import StackLayout
from kivy.clock import Clock

Builder.load_string('''
<ShowFPS>:
    size_hint_y: None
    height: self.minimum_height
    pos_hint: {'top': 1}
    Label:
        canvas:
            Color:
                rgba: (1, 0, 0, .5)
            Rectangle:
                pos: self.pos
                size: self.size
        id: show_fps
        size_hint_y: None
        height: dp(25)
        text_size: self.size
        halign: 'justify'
        valign: 'middle'
        text: 'FPS: 00'
''')

class ShowFPS(StackLayout):
    def __init__(self, root=None):
        super(ShowFPS, self).__init__()
        if not root:
            root = App.get_running_app().root_window
        root.add_widget(self)
        Clock.schedule_interval(self.update_fps, 1)

    def update_fps(self, x):
        self.ids.show_fps.text = 'FPS: {:05.2f} - {:05.2f}'.format(Clock.get_fps(), Clock.get_rfps())
