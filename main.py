from __future__ import division, absolute_import

import sys
import os

__version_info__ = (0, 1, 0)
__version__ = '0.1.0'
__app_name__ = 'Kivy RTC'

_dll = os.path.join('win-lib', 'bin')
os.environ["PATH"] += os.pathsep + _dll


if __name__ == '__main__':
    # Run preparation steps and fix errors when running on multi platform
    # such as: set KIVY_HOME, enable HiDPI, ...
    from utils.platform import pre_run_app

    # Delete all data of old version
    del_old_data = False
    pre_run_app(__app_name__, __version__, del_old_data)

    from utils.platform import PLATFORM, FIRST_RUN, IS_BINARY, IS_RELEASE,\
                                DATA_DIR

    if not IS_RELEASE:
        import logging
        logging.basicConfig(filename='janus.log')

    # Controlling the environment of Kivy
    # Those settings must match with settings in desktop.spec file
    # View more on https://kivy.org/doc/stable/guide/environment.html

    os.environ['KIVY_WINDOW'] = 'sdl2'
    # os.environ['KIVY_TEXT'] = 'sdl2'
    # os.environ['KIVY_VIDEO'] = 'ffpyplayer'
    os.environ['KIVY_AUDIO'] = 'sdl2,avplayer'
    # os.environ['KIVY_CAMERA'] = ''
    # os.environ['KIVY_IMAGE'] = 'sdl2,gif'
    # os.environ['KIVY_SPELLING'] = ''
    # os.environ['KIVY_CLIPBOARD'] = 'sdl2'

    # os.environ['KIVY_DPI'] = '110'
    # os.environ['KIVY_METRICS_DENSITY'] = '1'
    # os.environ['KIVY_METRICS_FONTSCALE'] = '1.2'

    # Debug OpenGL
    # os.environ['KIVY_GL_DEBUG'] = '1'

    import kivy

    # Apply settings of this app
    from utils import app_config

    # Add exception handler
    if IS_BINARY:
        from kivy.base import ExceptionManager
        from kivyrtc.tools.bug_reporter import BugHandler
        ExceptionManager.add_handler(BugHandler())

    kivy.require('1.11.0')
    from kivy.logger import Logger

    from kivyrtc.app import KivyRTCApp

    app = KivyRTCApp(__app_name__, DATA_DIR)

    if not IS_RELEASE:
        for name in logging.root.manager.loggerDict:
            if name == 'kivy':
                continue
            logging.getLogger(name).setLevel(logging.DEBUG)

    # Print important info of app
    Logger.info('App: Version: ' + __version__ +
                    (' Release' if IS_RELEASE else ' Debug'))
    Logger.info('App: First run: ' + str(FIRST_RUN))
    Logger.info('Kivy home: {}'.format(kivy.kivy_home_dir))
    Logger.info('Current working: {}'.format(os.getcwd()))
    Logger.info('App data: {}'.format(app.user_data_dir))
    Logger.info('Python paths: {}'.format(sys.path))
    from kivy.resources import resource_paths
    Logger.info('Resource paths: {}'.format(resource_paths))
    # from kivy.metrics import Metrics
    # Logger.info('DPI: {} {}'.format(Metrics.dpi, Metrics.dpi_rounded))

    app.run()
