# Kivy RTC

A simple video call for Kivy use [aiortc](https://github.com/aiortc/aiortc).

- *Note*:

    - Use python 3.7 or above.
    - **Currently, mobile is not supported.**
    - Camera use OpenCV, not use kivy camera provider.
    - Have some problems when handling audio.

Table of Contents:

[TOC]

**TODO**
    - Add new app icon in `kivyrtc/data` (replace existing file) and remove this todo.
    - Generate a new GUID for Inno setup when create new project and remove this todo.
    - When change version, remember change in files: main.py and buildtools/create-installer.iss
    - When you release app please change `IS_RELEASE` in utils/platform.py to `True` and remember change back to `False` when done it.

## Usage

### Launching the app

- Create env:

```bash
# On Mac, Linux
pip3 install --upgrade virtualenv
python3 -m virtualenv .env
source ./.env/bin/activate

# On Windows
py -3 -m pip install --upgrade virtualenv
py -3 -m virtualenv .env
.\.env\Scripts\activate
```

- Install lib:

    - On OS X run:

    ```bash
    brew install ffmpeg opus libvpx pkg-config
    ```

    - On Windows:

        - Download [Microsoft C++ Build tools](https://blogs.msdn.microsoft.com/pythonengineering/2016/04/11/unable-to-find-vcvarsall-bat/) to build PyAV, aiortc and opus.
        - You can copy include, lib folders in `win-lib` to `.env`, to avoid following the steps below.
        - Dowload [libvpx](https://github.com/ShiftMediaProject/libvpx/releases) and [ffmpeg](https://ffmpeg.zeranoe.com/builds/)(shared and dev) or build it yourself.
        - Extrack it and copy all content in folder `include` to `.env\Include` and `lib` to `.env\libs`.
        - Copy `path/to/lib/bin` to `os.environ["PATH"]` in main.py.
        - For opus you have to build it yourself because I can't find any builds. Download source [opus](http://opus-codec.org/downloads/) and extrack it in `%USERPROFILE%`.
        - Open `opus-1.3.1\win32\VS2015\opus.vcxproj`, find and add SDK version to:

        ```xml
        <PropertyGroup Condition="'$(Configuration)|$(Platform)'=='ReleaseDLL|x64'" Label="Configuration">
        <ConfigurationType>DynamicLibrary</ConfigurationType>
        <PlatformToolset>v140</PlatformToolset>
        <WindowsTargetPlatformVersion>Your Windows SDK version</WindowsTargetPlatformVersion>
        </PropertyGroup>
        ```

        - Build it by `Command Prompt for VS`: `msbuild "opus-1.3.1\win32\opus.vcxproj" /property:Configuration=ReleaseDLL;Platform=x64 /m /v:minimal`
        - Copy `x64\ReleaseDLL\opus.lib` to `.env\libs`, `opus-1.3.1\Include` to `.env\Include` and add `path/to/x64/ReleaseDLL/opus.dll` to `os.environ["PATH"]`.

- Install requirements and run:

```bash
pip install -r requirements.txt
python main.py
```

### Packaging project

**Make sure you follow all steps in [Environment preparing](https://kivy-skglobal.readthedocs.io/en/latest/#environment-preparing) and check all TODO**

- For Windows/MacOS, you must activate env and run pyinstaller:
    - Output folder will save in `dist` folder.
    - You must close app and the opened file or folder in `dist` folder before packaging app. If you not, pyinstaller can't build project.

```bash
# On Mac, Linux
source ./.env/bin/activate
# On Windows
.\.env\Scripts\activate
pyinstaller ./desktop.spec
```

- To create installer:
    - Windows: download [Inno Setup](http://www.jrsoftware.org/isinfo.php) and run `.\buildtools\create-installer.iss`. Output file will save in `.\buildtools\Output` folder.
    - Mac: run cmd `pkgbuild --install-location /Applications --component 'dist/Kivy RTC.app' 'dist/Install Kivy RTC v0.1.0.pkg'`

If you get error, read [this](https://kivy-skglobal.readthedocs.io/en/latest/development/packaging-project/) to fix it or contact to python@sk-global.biz for further instructions.

## Known issues
