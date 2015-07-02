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

#unity home path
UNITY_HOME = os.environ.get('UNITY_HOME')
if UNITY_HOME == None:
    print("Unity home path not found, please define it with an environment variable UNITY_HOME")
    sys.exit(1)
pass

if sys.platform.startswith("win32"):
    UNITY_EXE = os.path.join(UNITY_HOME, 'Unity.exe')
elif sys.platform.startswith("darwin"):
    UNITY_EXE = os.path.join(UNITY_HOME, 'Unity.app/Contents/MacOS/Unity')
else:
    print('Unsupported platform %s' %platform)
    sys.exit(1)
pass

if os.path.exists(UNITY_EXE):
    print('UnityPath: %s' %UNITY_EXE)
else:
    print("Unity installation not found")
    sys.exit(1)

#script home path
HOME = os.path.dirname(sys.argv[0])

def Init(projPath):
    Copy(os.path.join(HOME, 'BuildUtility/BuildUtility.cs'), os.path.join(projPath, 'Assets/Editor/__BuildUtility__.cs'))
    Copy(os.path.join(HOME, 'UnityInvoker/Assets/Editor/Invoker.cs'), os.path.join(projPath, 'Assets/Editor/__Invoker__.cs'))
    pass

def Cleanup(projPath):
    filePath = os.path.join(projPath, 'Assets/Editor/__BuildUtility__.cs')
    os.remove(filePath)
    os.remove(filePath + '.meta')

    filePath = os.path.join(projPath, 'Assets/Editor/__Invoker__.cs')
    os.remove(filePath)
    os.remove(filePath + '.meta')
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
            srcItem = os.path.join(src, item)
            dstItem = os.path.join(dst, item)
            if os.path.isfile(srcItem):
                shutil.copyfile(srcItem, dstItem)
            elif os.path.isdir(srcItem):
                Copy(srcItem, dstItem)
            else:
                pass
    elif os.path.isfile(src):
        dstDir = os.path.dirname(dst)
        if os.path.exists(dstDir) == False:
            os.makedirs(dstDir)
        shutil.copyfile(src, dst)
    pass

def RemoveFrom(src, dst):
    pass


projPath = os.path.join(HOME, 'UnityProject')

try:
    Init(projPath)
    ret = subprocess.call([UNITY_EXE,
                '-projectPath', projPath,
                '-batchmode', '-quit',
                '-executeMethod', 'Invoker.Invoke',
                'UnityEditor.EditorApplication.NewScene',
                '-next', 'UnityEngine.GameObject.CreatePrimitive', 'Cube',
                '-next', 'UnityEditor.EditorApplication.SaveScene', 'Assets/Example.unity',
                '-next', 'UnityEditor.PlayerSettings.bundleIdentifier', 'com.unityinvoker.example',
                '-next', 'UnityEditor.PlayerSettings.productName', 'UnityInvoker',
                '-next', 'UnityEditor.BuildPipeline.BuildPlayer', '[Assets/Example.unity]', '%s/Example.apk' %projPath, 'Android', 'None',
                '-next', 'UnityEditor.AssetDatabase.DeleteAsset', 'Assets/Example.unity'
                ])
finally:
    Cleanup(projPath)
