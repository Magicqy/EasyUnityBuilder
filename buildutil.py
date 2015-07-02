#!/usr/bin/python
import subprocess
import argparse
import datetime
import shutil
import sys
import os


'''
功能列表
	导出android/ios/win/osx的可执行文件
	导出XCode或者Eclipse工程
	在导出的XCode或者Eclipse工程的基础上生成ipa或者apk
	调用工程中的静态方法
	拷贝目录文件，用于设置plugins目录里的内容等
	SVN操作
	平台SDK集成
'''

#script home path
HOME = os.path.dirname(sys.argv[0])

#unity home path
UNITY_HOME = os.environ.get('UNITY_HOME')
if UNITY_HOME == None:
    print("Unity home path not found, please define it with an environment variable UNITY_HOME")
    sys.exit(1)

if sys.platform.startswith("win32"):
    UNITY_EXE = os.path.join(UNITY_HOME, 'Unity.exe')
elif sys.platform.startswith("darwin"):
    UNITY_EXE = os.path.join(UNITY_HOME, 'Unity.app/Contents/MacOS/Unity')
else:
    print('Unsupported platform: ', platform)
    sys.exit(1)

if os.path.exists(UNITY_EXE) == False:
    print("Unity installation not found at: ", UNITY_EXE)
    sys.exit(1)


#util methods
def Setup(projPath):
    Copy(os.path.join(HOME, 'BuildUtility/BuildUtility.cs'), os.path.join(projPath, 'Assets/Editor/_BuildUtility_/BuildUtility.cs'))
    Copy(os.path.join(HOME, 'BuildUtility/Invoker/Invoker.cs'), os.path.join(projPath, 'Assets/Editor/_BuildUtility_/Invoker.cs'))
    pass

def Cleanup(projPath):
    Del(os.path.join(projPath, 'Assets/Editor/_BuildUtility_'), True)
    pass

def Copy(src, dst):
    if src == dst or src == None or os.path.exists(src) == False:
        return

    src = os.path.abspath(os.path.expanduser(src))
    dst = os.path.abspath(os.path.expanduser(dst))

    if os.path.isdir(src):
        if os.path.exists(dst) == False:
            os.makedirs(dst)
        for item in os.listdir(src):
            srcPath = os.path.join(src, item)
            dstPath = os.path.join(dst, item)
            if os.path.isfile(srcPath):
                shutil.copyfile(srcPath, dstPath)
            elif os.path.isdir(srcPath):
                Copy(srcPath, dstPath)
            else:
                pass
    elif os.path.isfile(src):
        dstDir = os.path.dirname(dst)
        if os.path.exists(dstDir) == False:
            os.makedirs(dstDir)
        shutil.copyfile(src, dst)
    pass

def Del(path, alsoDelMetaFile = False):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    if alsoDelMetaFile:
        path += '.meta'
        if os.path.isfile(path):
            os.remove(path)
    pass

class Invoker:
    def __init__(self, methodName, *args):
        self.argList = ['-executeMethod', 'Invoker.Invoke', methodName]
        self.argList.extend(args)

    def Append(self, methodName, *args):
        self.argList.append('-next')
        self.argList.append(methodName)
        self.argList.extend(args)
        return self

    def Invoke(self, projPath, unityPath = UNITY_EXE, logFilePath = os.path.join(HOME, 'logFile.txt'), batch = True, quit = True):
        argList = [unityPath, '-logFile', logFilePath, '-projectPath', projPath]
        if batch:
            argList.append('-batchmode')
        if quit:
            argList.append('-quit')
        argList.extend(self.argList)

        print('UnityPath:       %s' %unityPath)
        print('projectPath:     %s' %projPath)
        print('logFilePath:     %s' %logFilePath)
        print('batchmode:       %s' %batch)
        print('quit:            %s' %quit)
        for arg in self.argList:
            if arg.startswith('-'):
                print('')
            print arg,
        print('')
        return subprocess.call(argList)
    pass

if __name__ == '__main__':
    try:
        projPath = os.path.join(HOME, 'UnityProject')
        Setup(projPath)

        ivk = Invoker('Invoker+LogWriter.logFilePath', os.path.join(HOME, 'invoker.txt'))
        ivk.Append('UnityEditor.EditorApplication.NewScene')
        ivk.Append('UnityEngine.GameObject.CreatePrimitive', 'Cube')
        ivk.Append('UnityEditor.EditorApplication.SaveScene', 'Assets/Example.unity')
        ivk.Append('UnityEditor.PlayerSettings.bundleIdentifier', 'com.unityinvoker.example')
        ivk.Append('UnityEditor.PlayerSettings.productName', 'UnityInvoker')
        ivk.Append('UnityEditor.BuildPipeline.BuildPlayer', '[Assets/Example.unity]', os.path.join(HOME, 'Example.apk'), 'Android', 'None')
        ivk.Append('UnityEditor.AssetDatabase.DeleteAsset', 'Assets/Example.unity')
        ivk.Invoke(projPath)

    finally:
        Cleanup(projPath)