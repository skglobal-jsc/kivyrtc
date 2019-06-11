'''
App config
==========

This module is used to configure app when the app first runs
and some configurations before launching app.

Warning: iOS actite flag KIVY_NO_CONFIG. If you want to keep those setting,
should run `del os.environ['KIVY_NO_CONFIG']` in main.py.

https://github.com/kivy/kivy-ios/blob/master/tools/templates/%7B%7B%20cookiecutter.project_name%20%7D%7D-ios/main.m#L39

'''

import sys
from kivy.config import Config
from kivy.logger import Logger
from utils.platform import PLATFORM, FIRST_RUN, IS_RELEASE

if FIRST_RUN:
    # Check this app import minimum imported module, as:
    # kivy kivy.compat kivy.logger kivy.utils
    # kivy.version kivy.deps kivy.config kivy.modules
    kivy_modules = 0
    for module in sys.modules.keys():
        if module.startswith('kivy'):
            # print(module)
            kivy_modules += 1
            if kivy_modules > 8 or any(
                        i in module for i in
                        ('core', 'uix', 'lang', 'graphics',
                        'input', 'app', 'factory')):
                Logger.warn('App config: Please check your code!\n'
                            'Those settings may not apply because you imported'
                            'module not in minimum imported module of kivy')
                break

    # To change those setting, read this:
    # https://kivy.org/doc/stable/api-kivy.config.html?highlight=config#available-configuration-tokens

    Config.set('kivy', 'log_level', 'info')
    # log_level: string, one of ‘trace’, ‘debug’, ‘info’, ‘warning’, ‘error’ or ‘critical’
    # Set the minimum log level to use.

    Config.set('kivy', 'log_name', 'kivy_%y-%m-%d_%_.log')
    # log_name: string
    # Format string to use for the filename of log file.

    Config.set('kivy', 'window_icon', '{{cookiecutter.repo_name}}/data/icon.png')
    # window_icon: string
    # Path of the window icon. Use this if you want to replace the default pygame icon.

    # Config.set('kivy', 'default_font', [
    #     'Roboto',
    #     'data/fonts/Roboto-Regular.ttf',
    #     'data/fonts/Roboto-Italic.ttf',
    #     'data/fonts/Roboto-Bold.ttf',
    #     'data/fonts/Roboto-BoldItalic.ttf'
    # ])
    # default_font: list
    # Default fonts used for widgets displaying any text.

    # Config.set('kivy', 'log_dir', 'logs')
    # log_dir: string
    # Path of log directory.

    # Config.set('kivy', 'log_enable', '1')
    # log_enable: int, 0 or 1
    # Activate file logging. 0 is disabled, 1 is enabled.

    # Config.set('kivy', 'keyboard_layout', 'qwerty')
    # keyboard_layout: string
    # Identifier of the layout to use.

    # Config.set('kivy', 'keyboard_mode', '')
    # keyboard_mode: string
    # Specifies the keyboard mode to use. If can be one of the following:
    # - '' - Let Kivy choose the best option for your current platform.
    # - 'system' - real keyboard.
    # - 'dock' - one virtual keyboard docked to a screen side.
    # - 'multi' - one virtual keyboard for every widget request.
    # - 'systemanddock' - virtual docked keyboard plus input from real keyboard.
    # - 'systemandmulti' - analogous.

    # Config.set('kivy', 'keyboard_repeat_delay', '300')
    # Config.set('kivy', 'keyboard_repeat_rate', '30')

    # Config.set('kivy', 'desktop', '1')
    # desktop: int, 0 or 1
    # This option controls desktop OS specific features,
    # such as enabling drag-able scroll-bar in scroll views,
    # disabling of bubbles in TextInput etc. 0 is disabled, 1 is enabled.

    # Config.set('kivy', 'exit_on_escape', '1')
    # exit_on_escape: int, 0 or 1
    # Enables exiting kivy when escape is pressed. 0 is disabled, 1 is enabled.

    # Config.set('kivy', 'pause_on_minimize', '0')
    # pause_on_minimize: int, 0 or 1
    # If set to 1, the main loop is paused and the on_pause event
    # is dispatched when the window is minimized.
    # This option is intended for desktop use only. Defaults to 0.

    # Config.set('kivy', 'kivy_clock', 'default')
    # kivy_clock: one of default, interrupt, free_all, free_only
    # The clock type to use with kivy.

    # Config.set('kivy', 'log_maxfiles', '100')
    # log_maxfiles: int
    # Keep log_maxfiles recent logfiles while purging the log directory.
    # Set 'log_maxfiles' to -1 to disable logfile purging (eg keep all logfiles).

    if PLATFORM in ('win', 'macosx'):
        from .resolution import get_resolution
        rsize = 0.85
        # size = get_resolution()
        # Config.set('graphics', 'width', int(size[1]*rsize/1.7777))
        # Config.set('graphics', 'height', int(size[1]*rsize))

    Config.set('graphics', 'minimum_width', '400')
    Config.set('graphics', 'minimum_height', '400')
    # Config.set('graphics', 'display', '-1')
    # Config.set('graphics', 'fullscreen', '0')
    # Config.set('graphics', 'left', '0')
    # Config.set('graphics', 'maxfps', '60')
    # Config.set('graphics', 'multisamples', '2')
    # Config.set('graphics', 'position', 'auto')
    # Config.set('graphics', 'rotation', '0')
    # Config.set('graphics', 'show_cursor', '1')
    # Config.set('graphics', 'top', '0')
    # Config.set('graphics', 'resizable', '1')
    # Config.set('graphics', 'borderless', '0')
    # Config.set('graphics', 'window_state', 'visible')
    # Config.set('graphics', 'min_state_time', '.035')
    # Config.set('graphics', 'allow_screensaver', '1')
    # Config.set('graphics', 'shaped', '0')

    if PLATFORM in ('win', 'macosx'):
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
    # Config.set('input', 'wm_touch', 'wm_touch')
    # Config.set('input', 'wm_pen', 'wm_pen')

    # Config.set('postproc', 'double_tap_distance', '20')
    # Config.set('postproc', 'double_tap_time', '250')
    # Config.set('postproc', 'ignore', '[]')
    # Config.set('postproc', 'jitter_distance', '0')
    # Config.set('postproc', 'jitter_ignore_devices', 'mouse,mactouch,')
    # Config.set('postproc', 'retain_distance', '50')
    # Config.set('postproc', 'retain_time', '0')
    # Config.set('postproc', 'triple_tap_distance', '20')
    # Config.set('postproc', 'triple_tap_time', '375')

    # Config.set('widgets', 'scroll_timeout', '250')
    # scroll_timeout: int
    # Default value of the scroll_timeout property used by the ScrollView widget.

    # Config.set('widgets', 'scroll_distance', '20')
    # scroll_distance: int
    # Default value of the scroll_distance property used by the ScrollView widget.

    # Should use App.build_config to create your own setting for your app
    # Read more on: https://kivy.org/doc/stable/api-kivy.app.html?highlight=config#kivy.app.App.build_config

    # To create your setting
    # Config.adddefaultsection('your_section')
    # Config.setdefault('you_section', 'your_key', 'your_data')

    Config.write()


# Only for debug
if not IS_RELEASE:
    # Config.set('modules', 'webdebugger', '1')
    # Config.set('modules', 'console', '1')
    Config.set('modules', 'inspector', '1')
    pass
