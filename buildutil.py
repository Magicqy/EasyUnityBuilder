#!/usr/bin/python
import os, sys, shutil, datetime, argparse, subprocess, plistlib

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

class GradleTask:
    Assemble = 'assemble'
    Install = 'install'
    UnInstall = 'uninstall'
    Lint = 'lint'
    Jar = 'jar'
    pass

class Workspace:
    @staticmethod
    def FullPath(path):
        return os.path.abspath(os.path.expanduser(path)) if path else ''

    extSwitch = {
        BuildTarget.Android : lambda ext, noexp: '.apk' if noexp and len(ext) == 0 else ext,
        BuildTarget.iPhone : lambda ext, noexp: ext,
        BuildTarget.StandaloneWindows : lambda ext, noexp: '/bin.exe' if len(ext) == 0 else ext,
        BuildTarget.StandaloneWindows64 : lambda ext, noexp: '/bin.exe' if len(ext) == 0 else ext,
        BuildTarget.StandaloneOSXIntel : lambda ext, noexp: '.app' if len(ext) == 0 else ext,
        BuildTarget.StandaloneOSXIntel64 : lambda ext, noexp: '.app' if len(ext) == 0 else ext,
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

def Copy(src, dst, append = False, stat = False):
    if src == dst or src == None or not os.path.exists(src):
        print('copy failed, %s >> %s' %(src, dst))
        sys.exit(1)

    if os.path.isdir(src):
        #src and dst are dirs
        if os.path.exists(dst):
            if os.path.isfile(dst):
                os.remove(dst)
            elif os.path.isdir(dst):
                if not append:
                    shutil.rmtree(dst)
                    os.makedirs(dst)
        else:
            os.makedirs(dst)
        
        for item in os.listdir(src):
            srcPath = os.path.join(src, item)
            dstPath = os.path.join(dst, item)
            Copy(srcPath, dstPath, append, stat)
    elif os.path.isfile(src):
        #src and dst are files
        if os.path.exists(dst):
            Del(dst)
        else:
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
                print(' '.join(argList))
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
                Copy(expDir, outPath, True)
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

def PackageAndroidCmd(args):
    projPath = Workspace.FullPath(args.projPath)
    gradlePath = os.path.join(args.homePath, 'gradlew')
    buildFile = Workspace.FullPath(args.bf) if args.bf else os.path.join(projPath, 'build.gradle')
    taskPrefix = args.pfx if args.pfx else ''
    taskSuffix = '%s%s' %(args.sfx[0].upper(), args.sfx[1:]) if args.sfx else ''
    argList = [os.path.join(gradlePath, 'gradlew.bat' if args.winOS else 'gradlew'), '-p', projPath, '-b', buildFile]
    if not args.ndp:
        argList.extend(['-P', 'targetProjDir=%s' %projPath,
                        '-P', 'buildDir=%s' %os.path.join(projPath, 'build'),
                        '-P', 'archivesBaseName=%s' %os.path.basename(projPath),])
    if args.prop:
        for item in args.prop:
            argList.append('-P')
            argList.append(item)
    
    if args.task:
        argList.extend(args.task)
    elif args.var:
        if args.pfx == None:
            if args.sfx == None:
                print('execute task with variants but prefix and suffix are not found')
            for var in args.var:
                argList.append('%s%s%s' %(taskPrefix, var, taskSuffix))
        else:
            for var in args.var:
                argList.append('%s%s%s%s' %(taskPrefix, var[0].upper(), var[1:], taskSuffix))
    else:
        print('no task to execute')
        sys.exit(1)

    if not os.path.isdir(projPath):
        print('project directory not exist: %s' %projPath)
        sys.exit(1)
    if not os.path.isfile(buildFile):
        print('build.gradle file not exist: %s' %buildFile)
        sys.exit(1)

    print('===Packge Android===')
    print('projectPath:     %s' %projPath)
    print('buildFile:       %s' %buildFile)
    print('')

    try:
        print(' '.join(argList))
        ret = subprocess.call(argList)
        if ret != 0:
            print('execute gradle task failed with retcode: %s' %ret)
            sys.exit(ret)
    except:
        print('package failed with excpetion')
    pass

def PackageiOSCmd(args):
    if args.winOS != False:
        print('package iOS only support on MacOS')
        sys.exit(1)

    projPath = Workspace.FullPath(args.projPath)
    buildType = 'Debug' if args.debug else 'Release'
    buildTarget = args.target
    buildSdk = str(args.sdk).lower()
    pkgOutFile = Workspace.FullPath(args.outFile) if args.outFile else projPath + '.ipa'
    productName = args.proName
    provProfile = None
    if args.provFile:
        provFile = Workspace.FullPath(args.provFile)
        if os.path.isfile(provFile):
            try:
                argList = ['security', 'cms', '-D', '-i', provFile]
                print(' '.join(argList))
                provStr = subprocess.check_output(argList)
                prov = plistlib.readPlistFromString(provStr)
                provProfile = prov['UUID']
                if productName == None:
                    productName = prov['Entitlements']['application-identifier'].split('.')[-1]
            except:
                print('get key values from provision file failed: %s' %provFile)
                sys.exit(1)
        else:
            print('provision file not exists: %s' %provFile)
            sys.exit(1)

    if provProfile == None:
        print('provision profile not found')
        sys.exit(1)    
    if not os.path.isdir(projPath):
        print('project directory not exist: %s' %projPath)
        sys.exit(1)

    print('===Package iOS===')
    print('projectPath:     %s' %projPath)
    print('buildType:       %s' %buildType)
    print('buildTarget:     %s' %buildTarget)
    print('buildSdk:        %s' %buildSdk)
    print('provision:       %s' %provProfile)
    print('productName:     %s' %productName)
    print('pkgOutFile:      %s' %pkgOutFile)
    print('')
    #try resolve the 'User Interaction Is Not Allowed' problem when run from shell
    if args.keychain:
        argList = ['security', 'unlock-keychain', '-p', args.keychain[1], Workspace.FullPath(args.keychain[0])]
        print(' '.join(argList))
        ret = subprocess.call(argList)
        if ret != 0:
            print('unlock keychain failed with retcode: %s' %ret)

    argList = ['xcodebuild',
               '-project', os.path.join(projPath, '%s.xcodeproj' %buildTarget),
               'clean',
               '-target', buildTarget,
               '-configuration', buildType]
    print(' '.join(argList))
    ret = subprocess.call(argList)
    if ret != 0:
        print('execute clean failed with retcode: %s' %ret)
        sys.exit(ret)

    argList = ['xcodebuild',
               '-project', os.path.join(projPath, '%s.xcodeproj' %buildTarget),
               '-sdk', buildSdk,
               '-target', buildTarget,
               '-configuration', buildType,
               'PROVISIONING_PROFILE=%s' %provProfile,
               'PRODUCT_NAME=%s' %productName,
               'DEPLOYMENT_POSTPROCESSING=YES',
               'STRIP_INSTALLED_PRODUCT=YES',
               'SEPARATE_STRIP=YES',
               'COPY_PHASE_STRIP=YES']
    if args.opt:
        argList.extend(args.opt)
    print(' '.join(argList))
    ret = subprocess.call(argList)
    if ret != 0:
        print('execute xcodebuild failed with retcode: %s' %ret)
        sys.exit(ret)
    
    #how to get archiveBaseName or bundle identifier?
    buildOutFile = os.path.join(projPath, 'build/%s-iphoneos/%s.app' %(buildType, productName))
    if not os.path.exists(buildOutFile):
        print('build output file not exist: %s' %buildOutFile)
        sys.exit(1)
    pkgFileDir = os.path.dirname(pkgOutFile)
    if not os.path.exists(pkgFileDir):
        os.makedirs(pkgFileDir)

    argList = ['/usr/bin/xcrun',
               '-sdk', buildSdk,
               'PackageApplication',
               '-v', buildOutFile,
               '-o', pkgOutFile
               #'--sign', signId,
               #'--embed', provFile
               ]
    print(' '.join(argList))
    ret = subprocess.call(argList)
    if ret != 0:
        print('execute xcrun failed with retcode: %s' %ret)
        sys.exit(ret)
    pass

def CopyCmd(args):
    src = Workspace.FullPath(args.src)
    dst = Workspace.FullPath(args.dst)

    print('===Copy===')
    print('src:     %s' %src)
    print('dst:     %s' %dst)
    print('append:  %s' %args.append)
    print('stat:    %s' %args.stat)

    Copy(src, dst, args.append, args.stat)
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
    build.add_argument('buildTarget', choices = ['android', 'ios', 'win', 'win64', 'osx', 'osx64'],
                       help = 'build target type')
    build.add_argument('outPath', help = 'build output path')
    build.add_argument('-opt', help = 'build options, see UnityEditor.BuildOptions for detail')
    build.add_argument('-exp', action = 'store_true', help = 'export project but not build it (android and ios only)')
    build.add_argument('-dev', action = 'store_true', help = 'development version, with debug symbols and enable profiler')
    build.add_argument('-aph', default = False, action = 'store_false',
                       help = 'keep android project hierarchy as outPath/{productName}/ instead of outPath/')
    build.set_defaults(func = BuildCmd)

    invoke = subparsers.add_parser('invoke', help = 'invoke method with arguments')
    invoke.add_argument('projPath', help = 'target unity project path')
    invoke.add_argument('methodName',
                        help = 'method name to invoke, [Assembly:(Optional)]Namespace.SubNamespace.Class+NestedClass.Method')
    invoke.add_argument('args', nargs = '*', help = 'method arguments, support types: primitive / string / enum')
    invoke.add_argument('-next', action = 'append', nargs = '+', help = 'next method and arguments to invoke')
    invoke.set_defaults(func = InvokeCmd)

    packandroid = subparsers.add_parser('packandroid', help = 'pacakge android project with gralde')
    packandroid.add_argument('projPath', help = 'target project path')
    packandroid.add_argument('-bf', help = 'specifies the build file', required = True)
    group = packandroid.add_mutually_exclusive_group(required = True)
    group.add_argument('-task', nargs = '+', help = 'full task names to execute')
    group.add_argument('-var', nargs = '+',
                       help = 'works together with task name prefix and suffix, the same as task {prefix}{Variant}{Suffix}')
    packandroid.add_argument('-pfx', help = 'task name prefix')
    packandroid.add_argument('-sfx', help = 'task name suffix')
    packandroid.add_argument('-prop', nargs = '*', help = 'additional gradle project properties')
    packandroid.add_argument('-ndp', action = 'store_true',
                     help = '''does not add default properties.
                     targetProjDir={projPath}, buildDir={projPath/build}, archivesBaseName={dirName(projPath)} by default.''')
    packandroid.set_defaults(func = PackageAndroidCmd)

    packios = subparsers.add_parser('packios', help = 'pacakge iOS project with xCode')
    packios.add_argument('projPath', help = 'target project path')
    packios.add_argument('-provFile', help = 'path of the .mobileprovision file', required = True)
    packios.add_argument('-outFile', help = 'package output file path', required = True)
    packios.add_argument('-proName', help = 'specifies the product name')
    packios.add_argument('-debug', action = 'store_true', help = 'build for Debug or Release')
    packios.add_argument('-target', default = 'Unity-iPhone', help = 'build target, Unity-iPhone by default')
    packios.add_argument('-sdk', default = 'iphoneos', help = 'build sdk version, latest iphoneos by default')
    packios.add_argument('-keychain', nargs = 2,
                     help = '''keychain path and passowrd.
                     unlock keychain (usually ~/Library/Keychains/login.keychain) to workaround for "User Interaction Is Not Allowed".
                     click 'Always Allow' button at first time it ask for keychain access''')
    packios.add_argument('-opt', nargs = '*',
                     help = '''additional build options.
                     PRODUCT_NAME={proName} DEPLOYMENT_POSTPROCESSING=YES, STRIP_INSTALLED_PRODUCT=YES, SEPARATE_STRIP=YES, COPY_PHASE_STRIP=YES by default.
                     check https://developer.apple.com/library/mac/documentation/DeveloperTools/Reference/XcodeBuildSettingRef for more information.''')
    packios.set_defaults(func = PackageiOSCmd)

    copy = subparsers.add_parser('copy', help = 'copy file or directory')
    copy.add_argument('src', help = 'path to copy from')
    copy.add_argument('dst', help = 'path to copy to')
    copy.add_argument('-append', default = False, action = 'store_true',
                      help = 'append files from src to dst instead of delete dst before copy, only take effect when copy directory.')
    copy.add_argument('-stat', default = False, action = 'store_true',
                      help = 'copy the permission bits, last access time, last modification time, and flags')
    copy.set_defaults(func = CopyCmd)

    delete = subparsers.add_parser('del', help = 'delete file or directory')
    delete.add_argument('src', help = 'path to delete')
    delete.add_argument('-sfx', nargs = '*', help = 'also delete path (src + suffix), useful for unity .meta files')
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
