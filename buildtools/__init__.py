import re
import os
from shutil import copyfile, copytree

__all__ = ('embedde_kivy_file', )

def embedde_kivy_file(path, build_path='./build/tmp'):
    if not os.path.exists(build_path):
        os.makedirs(build_path)
    copyfile('main.py', os.path.join(build_path, 'main.py'))
    copytree('utils', os.path.join(build_path, 'utils'))


    for root, _, files in os.walk(path):
        if root.split('/')[-1] == '__pycache__':
            continue

        if not os.path.exists(os.path.join(build_path, root)):
            os.makedirs(os.path.join(build_path, root))
        for file in files:
            if file.endswith(".pyc"):
                continue
            elif file.endswith(".py"):
                with open(os.path.join(root, file), 'r') as f:
                    data = f.read()
                    iterator = re.finditer(r'Builder.load_file\([\'"].*/(.*)[\'"][\),]',
                                            data)
                    n = 0
                    result = ''
                    for i in iterator:
                        with open(os.path.join(root,i.groups()[0]), 'r') as k:
                            kivy_data = k.read()
                            result += data[n:i.start()] +\
                                    'Builder.load_string(\'\'\'' +\
                                    kivy_data +\
                                    '\'\'\')'
                            n = i.end()
                    result += data[n:]
                    with open(os.path.join(build_path, root, file), "w+") as bf:
                        bf.write(result)
            else:
                pass
            #     if os.path.isfile(os.path.join(build_path, root, file)):
            #         copyfile(os.path.join(root, file), os.path.join(build_path, root, file))
    return build_path

if __name__ == "__main__":
    try:
        embedde_kivy_file('../kivyrtc')
    except Exception as e:
        raise(e)

