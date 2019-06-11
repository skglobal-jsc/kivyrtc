
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.textinput import TextInput
from kivy.logger import Logger

if __name__ == "__main__":
    from kivy.core.text import LabelBase, DEFAULT_FONT
    LabelBase.register(DEFAULT_FONT, '../data/MS Gothic.ttf')

    IME_Log = Logger.info
else:
    IME_Log = Logger.debug

class TextInputIME(TextInput):
    '''
    Textinput for non alphabet languages.

    Should run on SDL version 2.0.9

    For iOS, must apply this patch: https://github.com/Thong-Tran/kivy-ios/blob/fix-errors/recipes/sdl2/fix-non-alpabet.patch

    For Android, must apply this patch: https://github.com/Thong-Tran/python-for-android/blob/fix-error/pythonforandroid/bootstraps/sdl2/build/src/patches/SDLActivity.java.patch

    But it disables TYPE_TEXT_VARIATION_VISIBLE_PASSWORD (may leak data from the native textinput)
    '''

    def __init__(self, **kwargs):
        super(TextInputIME, self).__init__(**kwargs)
        self.bind(focus=self._active_ime)
        self.text = ''
        self._reset_ime()
        self._ignore_ime = False

    def _reset_ime(self):
        self._cache_text = None
        self._ime_text = None
        self._has_spacebar = False
        self._cursor_pos = None

    def _active_ime(self, instance, value):
        if value:
            Window.bind(on_textedit=self._on_text_ime)
        else:
            Window.unbind(on_textedit=self._on_text_ime)
            self.insert_text(self._ime_text if self._ime_text else u'')

    def _on_text_ime(self, ins, args):
        if isinstance(args, tuple):
            # IME_Log('IME: text, cursor, selection_len {}'.format(args))
            text = args[0]
        else:
            text = args

        # ignore same text and after press enter
        if self._ime_text == text or self._ignore_ime:
            self._ignore_ime = False
            IME_Log('IME: Ignore textedit: {}'.format(text))
            return True

        if not self._ime_text and self._cache_text is None:
            self.delete_selection()
            self._cache_text = self.text
            self._cursor_pos = self.cursor

        self._ime_text = text

        if self._ime_text == '':
            self.insert_text()
            IME_Log("IME: handle ''")
        else:
            self.insert_text(u'[{}]'.format(self._ime_text), reset_value=False)

        return True

    def insert_text(self, substring=None, from_undo=False, reset_value=True):
        ret = False
        if self._cache_text is not None:
            self.text = self._cache_text
            self.cursor = self._cursor_pos
            if substring:
                ret = super(TextInputIME, self).insert_text(substring, from_undo)
                IME_Log('IME: insert text {}'.format(substring))

            if reset_value:
                self._reset_ime()
        else:
            ret = super(TextInputIME, self).insert_text(substring, from_undo)

        return ret

    def keyboard_on_key_down(self, window, keycode, text, modifiers, dt=0):
        if self._ime_text:
            if self._has_spacebar and text and not text.isspace():
                IME_Log('IME: Key down: ignore text ' + text)
                return True

            elif keycode[1] in ('spacebar', 'tab'):
                self._has_spacebar = True
                IME_Log('IME: Key down: ignore spacebar')
                return True

            # Fix block Enter key on some Android keybroad
            elif platform == 'android' and\
                    keycode[1] == 'enter' and self._ignore_ime:
                self._ignore_ime = False
                self.insert_text(self._ime_text)
                IME_Log('IME: Key down: accept Enter')
                return True

            elif keycode[1] == 'enter':
                self._ignore_ime = True
                IME_Log('IME: Key down: ignore Enter')
                return True

            # Fix markedTextRange == None
            elif platform == 'ios' and keycode[1] == 'backspace':
                self.insert_text(self._ime_text[:-1])
                Logger.info('IME key down: ios backspace')
                return True

        return super(
            TextInputIME,
            self).keyboard_on_key_down(
            window,
            keycode,
            text,
            modifiers)


if __name__ == "__main__":
    from kivy.app import App
    from kivy.lang import Builder
    from kivy.logger import FileHandler

    class TApp(App):
        def on_start(self):
            if FileHandler.fd:
                FileHandler.fd.close()
                FileHandler.fd = open(FileHandler.filename, 'w', encoding='utf8')
        def build(self):
            return Builder.load_string('''
BoxLayout:
    TextInputIME:
        font_size: '22sp'
    TextInputIME:
        font_size: '22sp'
    ''')

    TApp().run()
