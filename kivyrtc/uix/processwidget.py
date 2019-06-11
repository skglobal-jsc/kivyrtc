from threading import Thread

from kivy.lang import Builder
from kivy.uix.modalview import ModalView
from kivy.properties import NumericProperty, BooleanProperty
from kivy.clock import Clock

Builder.load_string('''
<ProcessWidget>:
    canvas:
        Color:
            rgba: (0,0,0,1) if root.dark_theme else (1,1,1,1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: 10,10,10,10
    size_hint: (None, None)
    size: dp(220), dp(220)
    auto_dismiss: False
    FloatLayout:
        Widget:
            size_hint: None, None
            size: dp(30), dp(30)
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            canvas:
                Color:
                    rgba: .8,.8,.8,1
                Line:
                    circle: self.center_x, self.center_y, self.width
                    width: dp(3)

                Color:
                    rgba: 0.039, 0.584, 1.0,1
                Line:
                    circle: self.center_x, self.center_y, self.width, root.ang_s, root.ang_e, 500
                    width: dp(3)
        Label:
            text: "Please wait a moment"
            font_size: '17sp'
            pos_hint: {'center_x': 0.5, 'center_y': 0.25}
            color: (1,1,1,1) if root.dark_theme else (0,0,0,1)
        Button:
            size_hint: None, None
            size: dp(60), dp(30)
            pos_hint: {'center_x': 0.5, 'center_y': 0.1}
            text: "Cancel"
            on_release: root.stop_target()
            background_normal: 'blank.png'
            background_down: 'blank.png'
            font_size: '19sp'
            bold: True
            color: (1,1,1,1) if root.dark_theme else (0,0,0,1)
''')

class ProcessWidget(ModalView):
    dark_theme = BooleanProperty(False)
    ang_s = NumericProperty(0)
    ang_e = NumericProperty(14)

    vs = 7
    ve = 7

    maxc = 20
    counter = maxc
    step = 1

    def __init__(self, target=None, name=None, targs=(), tgkwargs={}, **kwargs):
        super(ProcessWidget, self).__init__(**kwargs)
        self.target = target
        self.thr = Thread(target=self.run_target,
                                        name=name, args=targs, kwargs=tgkwargs)

    def run_target(self, *args, **kwargs):
        self.target(*args, **kwargs)
        self.dismiss()

    def stop_target(self):
        self.thr.join(timeout=0.5)
        self.dismiss()

    def update_circle(self, dt):
        if not self.thr.is_alive():
            return

        if self.counter == self.maxc:
            if self.step == 1:
                self.step += 1
                self.vs = ProcessWidget.vs * 3
            elif self.step == 2:
                self.step += 1
                self.vs = ProcessWidget.vs
            elif self.step == 3:
                self.step += 1
                self.ve = ProcessWidget.vs * 3
            else:
                self.ve = ProcessWidget.ve
                self.step = 1

            self.counter = 0

        self.ang_e += self.vs
        self.ang_s += self.ve
        self.counter += 1
        Clock.schedule_once(self.update_circle, 1/32)

    def on_open(self):
        self.thr.start()
        Clock.schedule_once(self.update_circle, 1/32)


if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from time import sleep

    class MainApp(App):
        def build(self):
            layout = BoxLayout()
            btn = Button(text='Click me',
                                pos_hint={'center_x': 0.5, 'center_y': 0.5})
            btn.bind(on_release=lambda x:
                        ProcessWidget(target=lambda : sleep(10)).open())
            layout.add_widget(btn)

            return layout
    MainApp().run()
