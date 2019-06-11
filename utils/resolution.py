from .platform import PLATFORM

def get_resolution():
    '''
    Get visible frame for Windows, Mac.

    Should call this function after pre_run_app function called.
    '''
    width, height = 200, 200

    if PLATFORM == 'win':
        import ctypes
        user32 = ctypes.windll.user32
        width = int(user32.GetSystemMetrics(0))
        height = int(user32.GetSystemMetrics(1))
    elif PLATFORM == 'macosx':
        from pyobjus import autoclass
        from pyobjus.dylib_manager import load_framework, INCLUDE
        load_framework(INCLUDE.Cocoa)
        NSScreen = autoclass('NSScreen')
        mainScreen = NSScreen.mainScreen()
        width = int(mainScreen.visibleFrame.size.width)
        height = int(mainScreen.visibleFrame.size.height)

    return width, height
