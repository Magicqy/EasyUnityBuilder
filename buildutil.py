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
    print('Unity home path not found, please define it with an environment variable UNITY_HOME')
    sys.exit(1)

if sys.platform.startswith('win32'):
    UNITY_EXE = os.path.join(UNITY_HOME, 'Unity.exe')
elif sys.platform.startswith('darwin'):
    UNITY_EXE = os.path.join(UNITY_HOME, 'Unity.app/Contents/MacOS/Unity')
else:
    print('Unsupported platform: %s' %platform)
    sys.exit(1)

if os.path.exists(UNITY_EXE) == False:
    print('Unity installation not found at: %s' %UNITY_EXE)
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

class BuildTarget:
    Android = 'Android'
    iPhone = 'iPhone'
    StandaloneWindows = 'StandaloneWindows'
    StandaloneWindows64 = 'StandaloneWindows64'
    StandaloneOSXIntel = 'StandaloneOSXIntel'
    StandaloneOSXIntel64 = 'StandaloneOSXIntel64'
    
    btSwitch = {
        'android' : Android,
        'ios' : iPhone,
        'win' : StandaloneWindows,
        'win64' : StandaloneWindows64,
        'osx' : StandaloneOSXIntel,
        'osx64' : StandaloneOSXIntel64,
        }

    @staticmethod
    def From(targetStr):
        return BuildTarget.btSwitch[targetStr]
    pass

class PathUtil:
    @staticmethod
    def FullPath(path):
        return os.path.abspath(os.path.expanduser(path))

    extSwitch = {
        BuildTarget.Android : lambda e, o: '.apk' if o and len(e) == 0 else e,
        BuildTarget.iPhone : lambda e, o: '.ipa' if o and len(e) == 0 else e,
        BuildTarget.StandaloneWindows : lambda e, o: '/bin.exe' if len(e) == 0 else e,
        BuildTarget.StandaloneWindows64 : lambda e, o: '/bin.exe' if len(e) == 0 else e,
        BuildTarget.StandaloneOSXIntel : lambda e, o: '.app' if len(e) == 0 else e,
        BuildTarget.StandaloneOSXIntel64 : lambda e, o: '.app' if len(e) == 0 else e,
    }
    @staticmethod
    def CorrectExt(outPath, buildTarget, buildOpts):
        root, ext = os.path.splitext(outPath)
        return root + PathUtil.extSwitch[buildTarget](ext, buildOpts.find(BuildOptions.AcceptExternalModificationsToPlayer) < 0)

class BuildOptions:
    AcceptExternalModificationsToPlayer = 'AcceptExternalModificationsToPlayer'
    Development = 'Development'

    @staticmethod
    def From(opt, exp, dev):
        bo = str(opt)
        if exp:
            bo = '%s|%s' %(bo, BuildOptions.AcceptExternalModificationsToPlayer)
        if dev:
            bo = '%s|%s' %(bo, BuildOptions.Development)
        return bo
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

    def Invoke(self, projPath, unityPath = None, logFilePath = None, batch = True, quit = True):
        if unityPath == None:
            unityPath = UNITY_EXE
        if logFilePath == None:
            logFilePath = os.path.join(HOME, 'logFile.txt')
        
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
        print('')
        for i in range(2, len(self.argList)):
            arg = self.argList[i]
            if arg.startswith('-'):
                print('')
            else:
                print(arg),
        print('')
        
        try:
            Setup(projPath)
            print('')
            print(argList)
            return subprocess.call(argList)
        finally:
            Cleanup(projPath)
    pass

def ParseArgument(explicitArgs = None):
    #parse arguments
    parser = argparse.ArgumentParser(description = 'Build util for Unity')
    parser.add_argument('-unity', help = 'unity file path')
    parser.add_argument('-logFile', help = 'log file path')
    parser.add_argument('-nobatch', action = 'store_true', help = 'run unity without -batchmode')
    parser.add_argument('-noquit', action = 'store_true', help = 'run unity without -quit')

    subparsers = parser.add_subparsers(help = 'sub-command list')
    build = subparsers.add_parser('build', help='build player for unity project')
    build.add_argument('projPath', help = 'target unity project path')
    build.add_argument('buildTarget', choices = ['android', 'ios', 'win', 'win64', 'osx', 'osx64'], help = 'build target')
    build.add_argument('outPath', help = 'output file path')
    build.add_argument('-opt', help = 'build options, see UnityEditor.BuildOptions for detail')
    build.add_argument('-exp', action = 'store_true', help = 'export project but not build it (android and ios only)')
    build.add_argument('-dev', action = 'store_true', help = 'development version')
    build.set_defaults(func = BuildCmd)

    invoke = subparsers.add_parser('invoke', help = 'invoke method with arguments')
    invoke.add_argument('projPath', help = 'target unity project path')
    invoke.add_argument('methodName', help = 'method name to invoke')
    invoke.add_argument('args', nargs = '*', help = 'method arguments')
    invoke.set_defaults(func = InvokeCmd)

    return parser.parse_args(explicitArgs)
    '''
    parser.add_argument('-bakdsym', action = 'store_true', help = 'backup dsym file after build')
    parser.add_argument('--svn', default = 'skip', choices = ['skip', 'up', 'reup'],
	    help = 'svn checkout strategy, skip: do nothing; up:svn up, reup:svn revert then svn up')
    parser.add_argument('--keypwd', help = 'code sign keychain password, used to resolve problem: User Interaction Is Not Allowed')
    parser.add_argument('--keypath', help = 'code sign keychain path, used to resolve problem: User Interaction Is Not Allowed')
    parser.add_argument('-o', '--outpath', help = 'output path, without file extension')
    parser.add_argument('-t', '--buildtarget', default = 'android',
	    choices = ['ios', 'android', 'win', 'osx'], help= 'unity3d build target platform')
    parser.add_argument('-i', '--identifier', help = 'app identifier')
    parser.add_argument('-c', '--codesign', default = 'ep_dist',
	    choices = ['dev', 'dist', 'ep_dist'], help = 'code sign indentity and provision profile configuration')
    parser.add_argument('-v', '--vercode', type = int, help = 'app version code')
    parser.add_argument('-n', '--vername', help = 'app version name')
    parser.add_argument('-s', '--symbols', help = 'build with extra script symbols')
    parser.add_argument('-dev', action = 'store_true', help = 'development build')
    parser.add_argument('-method', help = 'execute method name')
    '''

def BuildCmd(args):
    projPath = PathUtil.FullPath(args.projPath)
    buildTarget = BuildTarget.From(args.buildTarget)
    buildOpts = BuildOptions.From(args.opt, args.exp, args.dev)
    outPath = PathUtil.CorrectExt(PathUtil.FullPath(args.outPath), buildTarget, buildOpts)

    #cleanup
    Del(outPath)
    if buildTarget == BuildTarget.StandaloneWindows or buildTarget == BuildTarget.StandaloneWindows64:
        Del(os.path.splitext(outPath)[0] + '_Data')

    dir = os.path.dirname(outPath)
    if not os.path.exists(dir):
        os.makedirs(dir)

    ivk = Invoker('BuildUtility.BuildPlayer', outPath, buildTarget, buildOpts)
    ivk.Invoke(projPath, args.unity, args.logFile, not args.nobatch, not args.noquit)
    pass

def InvokeCmd(args):
    ivk = Invoker(args.methodName, args.args)
    ivk.Invoke(projPath, args.unity, args.logFile, not args.nobatch, not args.noquit)
    pass

if __name__ == '__main__':
    args = ParseArgument('build ./UnityProject android ./android'.split())
    args.func(args)
    
    args = ParseArgument('build ./UnityProject ios ./ios'.split())
    args.func(args)
    
    args = ParseArgument('build ./UnityProject win ./win'.split())
    args.func(args)
    
    args = ParseArgument('build ./UnityProject osx ./osx'.split())
    args.func(args)
