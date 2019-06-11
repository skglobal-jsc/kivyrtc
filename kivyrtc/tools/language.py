'''
Source:
https://blog.fossasia.org/tag/language-localization/
'''


from kivy.lang import Observable
from kivy.logger import Logger
from os.path import join
import gettext


class ObservableTranslation(Observable):
    observers = []
    lang = None

    def __init__(self, default_lang, name_app):
        super(ObservableTranslation, self).__init__()
        self.ugettext = None
        self.lang = default_lang
        self.name_app = name_app
        self.switch_lang(self.lang)

    def _(self, text):
        return self.ugettext(text)

    def fbind(self, name, func, args, **kwargs):
        if name == "_":
            self.observers.append((func, args, kwargs))
        else:
            return super(ObservableTranslation, self).fbind(name, func, *args, **kwargs)

    def funbind(self, name, func, args, **kwargs):
        if name == "_":
            key = (func, args, kwargs)
            if key in self.observers:
                self.observers.remove(key)
        else:
            return super(ObservableTranslation, self).funbind(name, func, *args, **kwargs)

    def switch_lang(self, lang):
        # get the right locales directory, and instanciate a gettext
        locale_dir = join(self.name_app, 'data', 'locales')
        locales = gettext.translation('lang', locale_dir, languages=[lang])
        self.ugettext = locales.gettext

        # update all the kv rules attached to this text
        for func, largs, kwargs in self.observers:
            try:
                func(largs, None, None)
            except ReferenceError as e:
                pass
