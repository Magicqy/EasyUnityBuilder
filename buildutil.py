#!/usr/bin/python
import subprocess
import argparse
import datetime
import shutil
import sys
import os

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

    @staticmethod
    def AcceptExternalModifications(buildOpts):
        return buildOpts.find(BuildOptions.AcceptExternalModificationsToPlayer) >= 0
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

def Copy(src, dst, stat = False):
    if src == dst or src == None or not os.path.exists(src):
        print('copy failed, %s >> %s' %(src, dst))
        return

    if os.path.isdir(src):
        #src and dst are dirs
        if os.path.isfile(dst):
            os.remove(dst)
        if not os.path.exists(dst):
            os.makedirs(dst)
        
        for item in os.listdir(src):
            srcPath = os.path.join(src, item)
            dstPath = os.path.join(dst, item)
            if os.path.isfile(srcPath):
                shutil.copyfile(srcPath, dstPath)
                if stat:
                    shutil.copystat(srcPath, dstPath)
            elif os.path.isdir(srcPath):
                Copy(srcPath, dstPath, stat)
            else:
                print('path is not a file or directory: %s' %srcPath)
    elif os.path.isfile(src):
        #src and dst are files
        dstDir = os.path.dirname(dst)
        if not os.path.exists(dstDir):
            os.makedirs(dstDir)
        shutil.copyfile(src, dst)
        if stat:
            shutil.copystat(src, dst)
    else:
        print('path is not a file or directory: %s' %src)
    pass

def Del(path, alsoDelSuffixes = None):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        print('path is not a file or directory: %s' %path)

    if alsoDelSuffixes:
        for suffix in alsoDelSuffixes:
            Del(path + suffix)
    pass

class Invoker:
    def __init__(self, methodName, argList):
        self.argList = ['-executeMethod', 'Invoker.Invoke', methodName]
        self.argList.extend(argList)
        pass

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

        print('===Invoke===')
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
                    print('execute fail with retcode: %s' %ret)
                    sys.exit(ret)
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

    ivk = Invoker('BuildUtility.BuildPlayer', [outPath, buildTarget, buildOpts])
    ret = ivk.Invoke(projPath, args.homePath, args.unityExe, args.logFile, not args.nobatch, not args.noquit)
    
    #place exported project in outPath/ instead of outPath/productName/
    if ret == 0 and buildTarget == BuildTarget.Android and BuildOptions.AcceptExternalModifications(buildOpts) and not args.aph:
        for dir in os.listdir(outPath):
            expDir = os.path.join(outPath, dir)
            if os.path.isdir(expDir):
                Copy(expDir, outPath)
                Del(expDir)
                break
    pass

def InvokeCmd(args):
    projPath = Workspace.FullPath(args.projPath)
    
    ivk = Invoker(args.methodName, args.args)
    if args.next:
        for nlist in args.next:
            ivk.Append(nlist[0], nlist[1:])
    ivk.Invoke(projPath, args.homePath, args.unityExe, args.logFile, not args.nobatch, not args.noquit)
    pass

def PackageCmd(args):
    projPath = Workspace.FullPath(args.projPath)
    buildTarget = BuildTarget.From(args.buildTarget)
    buildType = 'debug' if args.debug else 'release'

    print('===Packge===')
    if not os.path.isdir(projPath):
        print('project directory not exist: %s' %projPath)
        return

    try:
        lastDir = os.getcwd()
        os.chdir(projPath)
        try:
            if buildTarget == BuildTarget.Android:
                if args.pf:
                    for flavor in args.pf:
                        GradleBuild(projPath, args.task, flavor, buildType, args.winOS)
                else:
                    GradleBuild(projPath, args.task, '', buildType, args.winOS)
            elif buildTarget == BuildTarget.iPhone:
                raise NotImplementedError
        except:
            print('package failed with excpetion')
    except:
        print('change working directory failed: %s' %projPath)
    finally:
        os.chdir(lastDir)
    pass

def GradleBuild(projPath, task, flavor, buildType, winOS):
    flavor = str(flavor).lower()
    buildType = str(buildType).lower()
    if len(buildType) > 1:
        argList = ['.\gradlew.bat' if winOS else './gradlew', '%s%s%s%s%s' %(task,
                                                 flavor[0].upper() if len(flavor) > 1 else '',
                                                 flavor[1:] if len(flavor) > 1 else '',
                                                 buildType[0].upper(),
                                                 buildType[1:])]
        print(argList)
        ret = subprocess.call(argList)
        if ret != 0:
            print('execute gradle task failed with retcode:%s' %ret)
            sys.exit(ret)
    else:
        print('invalid parameter, task:%s, flavor:%s, buildType:%s' %(task, flavor, buildType))
    pass

def CopyCmd(args):
    src = Workspace.FullPath(args.src)
    dst = Workspace.FullPath(args.dst)

    print('===Copy===')
    print('src:     %s' %src)
    print('dst:     %s' %dst)
    print('stat:    %s' %args.stat)

    Copy(src, dst, args.stat)
    pass

def DelCmd(args):
    path = Workspace.FullPath(args.src)

    print('===Delete===')
    print('path:    %s' %path)
    if args.sfx:
        for suffix in args.sfx:
            print('path:    %s%s' %(path, suffix))
    
    Del(path, args.sfx)
    pass

#parse arguments
def ParseArgs(explicitArgs = None):
    parser = argparse.ArgumentParser(description = 'build util for Unity')
    parser.add_argument('-unity', help = 'unity home path')
    parser.add_argument('-logFile', help = 'unity log file path')
    parser.add_argument('-nobatch', action = 'store_true', help = 'run unity without -batchmode')
    parser.add_argument('-noquit', action = 'store_true', help = 'run unity without -quit')

    subparsers = parser.add_subparsers(help = 'sub-command list')
    build = subparsers.add_parser('build', help='build player for unity project')
    build.add_argument('projPath', help = 'target unity project path')
    build.add_argument('buildTarget', choices = ['android', 'ios', 'win', 'win64', 'osx', 'osx64'], help = 'build target type')
    build.add_argument('outPath', help = 'output file path, with')
    build.add_argument('-opt', help = 'build options, see UnityEditor.BuildOptions for detail')
    build.add_argument('-exp', action = 'store_true', help = 'export project but not build it (android and ios only)')
    build.add_argument('-dev', action = 'store_true', help = 'development version, with debug symbols and enable profiler')
    build.add_argument('-aph', default = False, action = 'store_false', help = 'keep android project hierarchy as outPath/[productName]/ instead of outPath/')
    build.set_defaults(func = BuildCmd)

    invoke = subparsers.add_parser('invoke', help = 'invoke method with arguments')
    invoke.add_argument('projPath', help = 'target unity project path')
    invoke.add_argument('methodName', help = 'method name to invoke, [Assembly:(Optional)]Namespace.SubNamespace.Class+NestedClass.Method')
    invoke.add_argument('args', nargs = '*', help = 'method arguments, support types: primitive / string / enum')
    invoke.add_argument('-next', action = 'append', nargs = '+', help = 'next method and arguments to invoke')
    invoke.set_defaults(func = InvokeCmd)

    package = subparsers.add_parser('package', help = 'package exported project, use gradle as Android build system')
    package.add_argument('projPath', help = 'target project path')
    package.add_argument('buildTarget', choices = ['android', 'ios'], help = 'build target type')
    package.add_argument('-pf', nargs = '+', help = 'gradle productFlavors, defined in your build.gradle script')
    package.add_argument('-task', choices = ['assemble', 'install', 'uninstall', 'lint', 'jar'], default = 'assemble', help = 'gradle task name prefix')
    package.add_argument('-debug', default = False, action = 'store_true', help = 'debug build type, default is release')
    package.set_defaults(func = PackageCmd)

    copy = subparsers.add_parser('copy', help = 'copy file or directory')
    copy.add_argument('src', help = 'path to copy from')
    copy.add_argument('dst', help = 'path to copy to')
    copy.add_argument('-stat', default = False, action = 'store_true', help = 'copy the permission bits, last access time, last modification time, and flags')
    copy.set_defaults(func = CopyCmd)

    delete = subparsers.add_parser('del', help = 'delete file or directory')
    delete.add_argument('src', help = 'path to delete')
    delete.add_argument('-sfx', action = 'append', help = 'also delete path (src + suffix), useful for unity .meta files')
    delete.set_defaults(func = DelCmd)

    return parser.parse_args(explicitArgs)
    pass

def Run(args):
    #workspace home
    args.homePath = os.path.dirname(sys.argv[0])
    #unity home
    if args.unity == None:
        args.unity = os.environ.get('UNITY_HOME')
    args.unity = Workspace.FullPath(args.unity)

    if sys.platform.startswith('win32'):
        args.winOS = True
        args.unityExe = os.path.join(args.unity, 'Unity.exe')
    elif sys.platform.startswith('darwin'):
        args.winOS = False
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
    print('')
    pass

if __name__ == '__main__':
    if os.environ.get('DEV_LAUNCH'):
        print('=====DEV_LAUNCH=====')
        #Run(ParseArgs('copy ./1.txt ./2.txt'.split()))
        #Run(ParseArgs('del ./1.txt -ext .aa -ext .bb'.split()))
        #Run(ParseArgs('''invoke ./UnityProject PlayerSettings.bundleIdentifier com.buildutil.test
        #-next BuildUtility.AddSymbolForGroup Android ANDROID
        #-next BuildUtility.AddSymbolForGroup iPhone IOS'''.split()))
        #Run(ParseArgs('build ./UnityProject android ./android'.split()))
        #Run(ParseArgs('build ./UnityProject ios ./ios'.split()))
        #Run(ParseArgs('build ./UnityProject win ./win'.split()))   
        #Run(ParseArgs('build ./UnityProject osx ./osx'.split()))
    else:
        Run(ParseArgs())
    pass
