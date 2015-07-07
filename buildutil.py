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

class Workspace:
    @staticmethod
    def FullPath(path):
        return os.path.abspath(os.path.expanduser(path)) if path else ''

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
        return root + Workspace.extSwitch[buildTarget](ext, buildOpts.find(BuildOptions.AcceptExternalModificationsToPlayer) < 0)
    pass

#util methods
def Setup(projPath, homePath):
    Copy(os.path.join(homePath, 'BuildUtility/BuildUtility.cs'), os.path.join(projPath, 'Assets/Editor/_BuildUtility_/BuildUtility.cs'))
    Copy(os.path.join(homePath, 'BuildUtility/Invoker/Invoker.cs'), os.path.join(projPath, 'Assets/Editor/_BuildUtility_/Invoker.cs'))
    pass

def Cleanup(projPath):
    Del(os.path.join(projPath, 'Assets/Editor/_BuildUtility_'), ['.meta'])
    pass

def Copy(src, dst):
    if src == dst or src == None or os.path.exists(src) == False:
        print('copy failed, %s >> %s' %(src, dst))
        return

    if os.path.isdir(src):
        #src and dst are dir
        if os.path.isfile(dst):
            os.remove(dst)
        if not os.path.exists(dst):
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
        #src and dst are file
        dstDir = os.path.dirname(dst)
        if os.path.exists(dstDir) == False:
            os.makedirs(dstDir)
        shutil.copyfile(src, dst)
    pass

def Del(path, alsoDelFileWithExts = None):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    if alsoDelFileWithExts:
        for ext in alsoDelFileWithExts:
            newFile = path + ext
            if os.path.isfile(newFile):
                os.remove(newFile)
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

    def Append(self, methodName, argList):
        self.argList.append('-next')
        self.argList.append(methodName)
        self.argList.extend(argList)
        return self

    def Invoke(self, projPath, homePath, unityExe, logFilePath, batch = True, quit = True):
        argList = [unityExe, '-logFile', logFilePath, '-projectPath', projPath]
        if batch:
            argList.append('-batchmode')
        if quit:
            argList.append('-quit')
        argList.extend(self.argList)

        print('unityPath:       %s' %unityExe)
        print('projectPath:     %s' %projPath)
        print('logFilePath:     %s' %logFilePath)
        print('batchmode:       %s' %batch)
        print('quit:            %s' %quit)
        print('')
        for i in range(2, len(self.argList)):
            arg = self.argList[i]
            if isinstance(arg, list):
                arg = '%s' %' '.join(arg)
            if arg.startswith('-'):
                print('')
            else:
                print(arg),
        print('')
        
        if os.path.isdir(projPath):
            try:
                Setup(projPath, homePath)
                print('')
                print(argList)
                ret = subprocess.call(argList)
                if ret != 0:
                    print('execute fail with retcode: %s' %s)
                return ret
            finally:
                Cleanup(projPath)
        else:
            print('projectPath not exist: %s' %projPath)
    pass

def BuildCmd(args):
    projPath = Workspace.FullPath(args.projPath)
    buildTarget = BuildTarget.From(args.buildTarget)
    buildOpts = BuildOptions.From(args.opt, args.exp, args.dev)
    outPath = Workspace.CorrectExt(Workspace.FullPath(args.outPath), buildTarget, buildOpts)

    #cleanup
    Del(outPath)
    if buildTarget == BuildTarget.StandaloneWindows or buildTarget == BuildTarget.StandaloneWindows64:
        Del(os.path.splitext(outPath)[0] + '_Data')

    dir = os.path.dirname(outPath)
    if not os.path.exists(dir):
        os.makedirs(dir)

    ivk = Invoker('BuildUtility.BuildPlayer', outPath, buildTarget, buildOpts)
    ivk.Invoke(projPath, args.homePath, args.unityExe, args.logFile, not args.nobatch, not args.noquit)
    pass

def InvokeCmd(args):
    projPath = Workspace.FullPath(args.projPath)
    
    ivk = Invoker(args.methodName, args.args)
    if args.next:
        for nlist in args.next:
            ivk.Append(nlist[0], nlist[1:])
    ivk.Invoke(projPath, args.homePath, args.unityExe, args.logFile, not args.nobatch, not args.noquit)
    pass

def CopyCmd(args):
    args.src = Workspace.FullPath(args.src)
    args.dst = Workspace.FullPath(args.dst)
    print('copy:')
    print('src: %s' %args.src)
    print('dst: %s' %args.dst)

    Copy(args.src, args.dst)
    pass

def DelCmd(args):
    args.src = Workspace.FullPath(args.src)
    print('delete:')
    print(args.src)
    if args.ext:
        for ext in args.ext:
            print('%s%s' %(args.src, ext))

    Del(args.src, args.ext)
    pass

#parse arguments
def ParseArgs(explicitArgs = None):
    parser = argparse.ArgumentParser(description = 'build util for Unity')
    parser.add_argument('-unity', help = 'unity home path')
    parser.add_argument('-logFile', help = 'log file path')
    parser.add_argument('-nobatch', action = 'store_true', help = 'run unity without -batchmode')
    parser.add_argument('-noquit', action = 'store_true', help = 'run unity without -quit')

    subparsers = parser.add_subparsers(help = 'sub-command list')
    build = subparsers.add_parser('build', help='build player for unity project')
    build.add_argument('projPath', help = 'target unity project path')
    build.add_argument('buildTarget', choices = ['android', 'ios', 'win', 'win64', 'osx', 'osx64'], help = 'build target')
    build.add_argument('outPath', help = 'output file path, with')
    build.add_argument('-opt', help = 'build options, see UnityEditor.BuildOptions for detail')
    build.add_argument('-exp', action = 'store_true', help = 'export project but not build it (android and ios only)')
    build.add_argument('-dev', action = 'store_true', help = 'development version, with debug symbols and enable profiler')
    build.set_defaults(func = BuildCmd)

    invoke = subparsers.add_parser('invoke', help = 'invoke method with arguments')
    invoke.add_argument('projPath', help = 'target unity project path')
    invoke.add_argument('methodName', help = 'method name to invoke, [Assembly:(Optional)]Namespace.SubNamespace.Class+NestedClass.Method')
    invoke.add_argument('args', nargs = '*', help = 'method arguments, support types: primitive / string / enum')
    invoke.add_argument('-next', action = 'append', nargs = '+', help = 'next method and arguments to invoke')
    invoke.set_defaults(func = InvokeCmd)

    copy = subparsers.add_parser('copy', help = 'copy file and directory')
    copy.add_argument('src', help = 'path to copy from')
    copy.add_argument('dst', help = 'path to copy to')
    copy.set_defaults(func = CopyCmd)

    delete = subparsers.add_parser('del', help = 'delete file and directory')
    delete.add_argument('src', help = 'path to delete')
    delete.add_argument('-ext', action = 'append', help = 'src path + ext will also be delete, useful for unity .meta files')
    delete.set_defaults(func = DelCmd)

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
    pass

def Run(args):
    #workspace home
    args.homePath = os.path.dirname(sys.argv[0])
    #unity home
    if args.unity == None:
        args.unity = os.environ.get('UNITY_HOME')
    args.unity = Workspace.FullPath(args.unity)

    if sys.platform.startswith('win32'):
        args.unityExe = os.path.join(args.unity, 'Unity.exe')
    elif sys.platform.startswith('darwin'):
        args.unityExe = os.path.join(args.unity, 'Unity.app/Contents/MacOS/Unity')
    else:
        print('Unsupported platform: %s' %sys.platform)
        sys.exit(1)

    if not os.path.exists(args.unity):
        print('Unity home path not found, use -unity argument or define it with an environment variable UNITY_HOME')
        sys.exit(1)
    if not os.path.exists(args.unityExe):
        print('Unity installation not found at: %s' %args.unityExe)
        sys.exit(1)
    
    #log file
    if args.logFile == None:
        args.logFile = os.path.join(args.homePath, 'logFile.txt')
    args.logFile = Workspace.FullPath(args.logFile)
    dir = os.path.dirname(args.logFile)
    if not os.path.exists(dir):
        os.makedirs(dir)
    args.func(args)
    pass

if __name__ == '__main__':
    if os.environ.get('DEV_LAUNCH'):
        print('=====DEV_LAUNCH=====')
        #Run(ParseArgs('copy ./1.txt ./2.txt'.split()))
        #Run(ParseArgs('del ./1.txt -ext .aa -ext .bb'.split()))
        #Run(ParseArgs('''invoke ./UnityProject PlayerSettings.bundleIdentifier com.buildutil.test
        #-next BuildUtility.AddSymbolForGroup Android ANDROID
        #-next BuildUtility.AddSymbolForGroup iPhone IOS'''.split()))
        Run(ParseArgs('build ./UnityProject android ./android'.split()))
        #Run(ParseArgs('build ./UnityProject ios ./ios'.split()))
        #Run(ParseArgs('build ./UnityProject win ./win'.split()))   
        #Run(ParseArgs('build ./UnityProject osx ./osx'.split()))
    else:
        Run(ParseArgs())
    pass