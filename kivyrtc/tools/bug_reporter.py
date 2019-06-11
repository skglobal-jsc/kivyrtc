
from os.path import abspath, dirname, join, realpath
import sys
import traceback

from kivy.app import App
from kivy.base import ExceptionHandler, ExceptionManager
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.utils import platform
from kivy import __version__
from kivy.logger import LoggerHistory, FileHandler

__all__ = ('BugHandler', )

Builder.load_file(abspath(
            join(dirname(__file__),'bug_reporter.kv')))


class ReportWarning(Popup):
    text = StringProperty('')
    '''Warning Message
    '''

    __events__ = ('on_release',)

    def on_release(self, *args):
        pass


class BugReporter(FloatLayout):
    txt_traceback = ObjectProperty(None)
    log_app = ObjectProperty(None)
    '''TextView to show the traceback message
    '''

    def __init__(self, **kw):
        super(BugReporter, self).__init__(**kw)
        self.warning = None

        self.ids.tab_wg.bind(current_tab=self.change_bt)

    def change_bt(self, ins, current):
        self.ids.copy_bt.text = 'Copy ' + self.ids.tab_wg.current_tab.text

    def on_clipboard(self, *args):
        '''Event handler to "Copy to Clipboard" button
        '''
        if self.ids.tab_wg.current_tab.text == 'Traceback':
            Clipboard.copy(self.txt_traceback.text)
        else:
            Clipboard.copy(self.log_app.text)

    def on_report(self, *args):
        '''Event handler to "Report Bug" button
        '''
        warning = ReportWarning()
        warning.text = ('Warning. Some web browsers doesn\'t post the full'
                        ' traceback error. \n\nPlease, check if the last line'
                        ' of your report is "End of Traceback". \n\n'
                        'If not, use the "Copy to clipboard" button the get'
                        'the full report and post it manually."')
        warning.open()
        self.warning = warning

    def on_close(self, *args):
        '''Event handler to "Close" button
        '''
        App.get_running_app().stop()


class BugReporterApp(App):
    traceback = StringProperty('')

    def __init__(self, **kw):
        # self.traceback = traceback
        super(BugReporterApp, self).__init__(**kw)

    def build(self):
        rep = BugReporter()
        template = '''
## Environment Info

{}

## Traceback

```
{}
```

End of Traceback
'''
        env_info = 'Platform: ' + platform
        env_info += '\nPython: v{}'.format(sys.version)
        env_info += '\nKivy: v{}'.format(__version__)

        if isinstance(self.traceback, bytes):
            encoding = sys.getfilesystemencoding()
            if not encoding:
                encoding = sys.stdin.encoding
            if encoding:
                self.traceback = self.traceback.decode(encoding)
        rep.txt_traceback.text = template.format(env_info, self.traceback)

        got_log = False
        if FileHandler.fd:
            try:
                with open(FileHandler.fd.name, 'r') as f:
                    rep.log_app.text = f.read()
                got_log = True
            except:
                pass
        if not got_log:
            rep.log_app.text = ''
            for i in LoggerHistory.history:
                rep.log_app.text += i.message + '\n'

        return rep


class BugHandler(ExceptionHandler):

    raised_exception = False
    '''Indicates if the BugReporter has already raised some exception
    '''

    def handle_exception(self, inst):
        if self.raised_exception:
            return ExceptionManager.PASS
        App.get_running_app().stop()
        if isinstance(inst, KeyboardInterrupt):
            return ExceptionManager.PASS
        else:
            for child in Window.children:
                Window.remove_widget(child)
            self.raised_exception = True
            Window.fullscreen = False
            bapp = BugReporterApp(traceback=traceback.format_exc())
            bapp.run()
            return ExceptionManager.PASS


if __name__ == '__main__':
    from os.path import join, abspath, dirname
    from kivy.resources import resource_add_path
    resource_add_path(
        abspath(join(dirname(__file__), '..', 'data')))

    BugReporterApp(traceback='Bug example').run()
