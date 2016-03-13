#!/usr/bin/python
import sys, os, time
import buildutil as utl

start = time.time()

UNITY_PROJ = 'TestProject'
BUILD_PATH = os.path.join(UNITY_PROJ, 'Builds')
XCODE_PROJ = os.path.join(BUILD_PATH, 'xproj')
OUT_FILE = os.path.join(BUILD_PATH, 'output.ipa')

BUNDLE_ID = 'com.test.proj'
PROV_FILE = '{mobileprovision file path}'
KEY_CHAIN = ['{codesgin keychain file path}}', '{codesign keychain password}']

shared_args = dict(
    log = os.path.join(BUILD_PATH, 'build.log'),
    ulog = os.path.join(BUILD_PATH, 'unity.log')
)

utl.runTask(utl.INVOKE, shared_args,
    projPath = UNITY_PROJ,
    calls = [['UnityEditor.PlayerSettings.bundleIdentifier', BUNDLE_ID]])

utl.runTask(utl.BUILD, shared_args,
    projPath = UNITY_PROJ,
    buildTarget = 'ios',
    outPath = XCODE_PROJ)
    
utl.runTask(utl.PACK_IOS, shared_args,
    projPath = XCODE_PROJ,
    outFile = OUT_FILE,
    provFile = PROV_FILE,
    keychain = KEY_CHAIN)

print('===time passed===')
print(time.time()-start)