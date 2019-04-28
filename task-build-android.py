#!/usr/bin/python
import sys, os, time
import buildutil as utl

start = time.time()

UNITY_PROJ = './TestProject'
BUILD_PATH = os.path.join(UNITY_PROJ, 'Builds')
EXPORT_PROJ = os.path.join(BUILD_PATH, 'android-proj')

BUNDLE_ID = 'com.test.proj'

shared_args = dict(
    # unityHome = 'UNITY_HOME_PATH',
    unityLog = os.path.join(BUILD_PATH, 'unity.log'),
    log = os.path.join(BUILD_PATH, 'build.log'),
)

utl.runTask(utl.INVOKE, shared_args,
    projPath = UNITY_PROJ,
    calls = [['UnityEditor.PlayerSettings.bundleIdentifier', BUNDLE_ID]])

utl.runTask(utl.BUILD, shared_args,
    projPath = UNITY_PROJ,
    buildTarget = 'android',
    outPath = EXPORT_PROJ,
    exp = True)
    
utl.runTask(utl.PACK_ANDROID, shared_args,
    projPath = EXPORT_PROJ,
    task = 'assembleRelease')

print('===time passed===')
print(time.time()-start)