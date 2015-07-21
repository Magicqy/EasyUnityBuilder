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

    @staticmethod
    def GetKeyValuesFromProvXml(provXml):
        lines = str(provXml).splitlines()
        for i in xrange(0, len(lines)):
            lines[i] = lines[i].strip()
            
        idx = lines.index('<key>com.apple.developer.team-identifier</key>')
        teamId = str(lines[idx + 1])[len('<string>') : -len('</string>')]

        idx = lines.index('<key>application-identifier</key>')
        bundleId = str(lines[idx + 1])[len('<string>') + len(teamId) + 1 : -len('</string>')]    
        
        idx = lines.index('<key>TeamName</key>')
        teamName = str(lines[idx + 1])[len('<string>') : -len('</string>')]

        idx = lines.index('<key>UUID</key>')
        uuid = str(lines[idx + 1])[len('<string>') : -len('</string>')]
        return bundleId, teamName, uuid
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

def PackageAndroidCmd(args):
    projPath = Workspace.FullPath(args.projPath)
    gradlePath = os.path.join(args.homePath, 'gradlew')
    buildFile = Workspace.FullPath(args.bf) if args.bf else os.path.join(projPath, 'build.gradle')
    buildType = 'Debug' if args.debug else 'Release'
    taskPrefix = args.task
    argList = [os.path.join(gradlePath, 'gradlew.bat' if args.winOS else 'gradlew'), '-p', projPath, '-b', buildFile]
    if not args.ndp:
        argList.extend(['-P', 'targetProjDir=%s' %projPath,
                        '-P', 'buildDir=%s' %os.path.join(projPath, 'build'),
                        '-P', 'archivesBaseName=%s' %os.path.basename(projPath),])
    if args.prop:
        for kv in args.prop:
            argList.append('-P')
            argList.append(kv)
    if args.pf:
        for flavor in args.pf:
            argList.append('%s%s%s%s' %(taskPrefix, flavor[0].upper(), flavor[1:], buildType))
    else:
        argList.append('%s%s' %(taskPrefix, buildType))

    if not os.path.isdir(projPath):
        print('project directory not exist: %s' %projPath)
        return
    if not os.path.isfile(buildFile):
        print('build.gradle file not exist: %s' %buildFile)
        return

    print('===Packge Android===')
    print('projectPath:     %s' %projPath)
    print('buildFile:       %s' %buildFile)
    print('buildType:       %s' %buildType)
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
    bundleId = None
    if args.provFile:
        provFile = Workspace.FullPath(args.provFile)
        if os.path.isfile(provFile):
            try:
                argList = ['security', 'cms', '-D', '-i', provFile]
                print(' '.join(argList))
                provXml = subprocess.check_output(argList)
                bundleId, signId, provId = Workspace.GetKeyValuesFromProvXml(provXml)
            except:
                print('get key values from provision file failed: %s' %provFile)
                sys.exit(1)
        else:
            print('provision file not exists: %s' %provFile)
            sys.exit(1)
    elif args.provUUID:
        provId = args.provUUID
        signId = args.signId
    
    if not os.path.isdir(projPath):
        print('project directory not exist: %s' %projPath)
        return

    print('===Package iOS===')
    print('projectPath:     %s' %projPath)
    print('buildType:       %s' %buildType)
    print('buildTarget:     %s' %buildTarget)
    print('buildSdk:        %s' %buildSdk)
    print('provision:       %s' %provId)
    print('codeSign:        %s' %signId)
    print('bundleId:        %s' %bundleId)
    print('')
    #try resolve the 'User Interaction Is Not Allowed' problem when run from shell
    if args.keychain:
        ret = subprocess.call(['security', 'unlock-keychain', '-p', args.keychain[1], Workspace.FullPath(args.keychain[0])])
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
               'PROVISIONING_PROFILE=%s' %provId,
               'CODE_SIGN_IDENTITY="%s"' %signId,
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
    baseName = ''
    buildDir = os.path.join(projPath, 'build/%s-iphoneos' %buildType)
    if bundleId:
        baseName = bundleId.split('.')[-1]
    else:
        if os.path.isdir(buildDir):
            for item in os.listdir(buildDir):
                name, ext = os.path.splitext(item)
                if ext == '.app':
                    print('base name found by %s' %item)
                    baseName = name
        else:
            print('build output directory not found: %s' %buildDir)
            sys.exit(1)

    argList = ['/usr/bin/xcrun',
               '-sdk', buildSdk,
               'PackageApplication',
               '-v', os.path.join(buildDir, '%s.app' %baseName),
               '-o', '%s.ipa' %projPath
               #'--sign', BuildArgs[K_CODE_SIGN_INFO][args.codesign][K_CODE_SIGN_ID],
               #'--embed', '/Users/Shared/Jenkins/Downloads/xxx/xxx.mobileprovision'
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
    build.add_argument('outPath', help = 'build output path')
    build.add_argument('-opt', help = 'build options, see UnityEditor.BuildOptions for detail')
    build.add_argument('-exp', action = 'store_true', help = 'export project but not build it (android and ios only)')
    build.add_argument('-dev', action = 'store_true', help = 'development version, with debug symbols and enable profiler')
    build.add_argument('-aph', default = False, action = 'store_false', help = 'keep android project hierarchy as outPath/{productName}/ instead of outPath/')
    build.set_defaults(func = BuildCmd)

    invoke = subparsers.add_parser('invoke', help = 'invoke method with arguments')
    invoke.add_argument('projPath', help = 'target unity project path')
    invoke.add_argument('methodName', help = 'method name to invoke, [Assembly:(Optional)]Namespace.SubNamespace.Class+NestedClass.Method')
    invoke.add_argument('args', nargs = '*', help = 'method arguments, support types: primitive / string / enum')
    invoke.add_argument('-next', action = 'append', nargs = '+', help = 'next method and arguments to invoke')
    invoke.set_defaults(func = InvokeCmd)

    package = subparsers.add_parser('package', help = 'package exported project, use gradle as Android build system')
    package.add_argument('projPath', help = 'target project path')
    packageSp = package.add_subparsers(help = 'package sub parsers')
    par = packageSp.add_parser('android', help = 'pacakge android project with gralde')
    par.add_argument('-bf', help = 'specifies the build file')
    par.add_argument('-pf', nargs = '+', help = 'specifies the gradle productFlavors')
    par.add_argument('-task', choices = ['assemble', 'install', 'uninstall', 'lint', 'jar'], default = 'assemble', help = 'gradle task name prefix')
    par.add_argument('-debug', action = 'store_true', help = 'build for Debug or Release')
    par.add_argument('-prop', nargs = '+', help = 'add gradle project property')
    par.add_argument('-ndp', action = 'store_true', help = '''does not add default properties
    targetProjDir={projPath}, buildDir={projPath/build}, archivesBaseName={dirName(projPath)}''')
    par.set_defaults(func = PackageAndroidCmd)

    par = packageSp.add_parser('ios', help = 'pacakge iOS project with xCode')
    group = par.add_mutually_exclusive_group(required = True)
    group.add_argument('-provFile', help = 'path of the .mobileprovision file')
    group.add_argument('-provUUID', help = 'UUID of the provision profile')
    par.add_argument('-signId', default = 'Automatic', help = 'code sign identity such as "Apple Distribution: xxx..xxx..xxx", Automatic by default')
    par.add_argument('-debug', action = 'store_true', help = 'build for Debug or Release')
    par.add_argument('-target', default = 'Unity-iPhone', help = 'build target, Unity-iPhone by default')
    par.add_argument('-sdk', default = 'iphoneos8.2', help = 'build sdk version, iphoneos8.2 by default')
    par.add_argument('-keychain', nargs = 2, help = 'keychain path and passowrd, unlock keychain (usually ~/Library/Keychains/login.keychain) to workaround when "User Interaction Is Not Allowed"')
    par.add_argument('-opt', nargs = '+', help = '''additional build options.
    DEPLOYMENT_POSTPROCESSING=YES, STRIP_INSTALLED_PRODUCT=YES, SEPARATE_STRIP=YES, COPY_PHASE_STRIP=YES by default''')
    par.set_defaults(func = PackageiOSCmd)

    copy = subparsers.add_parser('copy', help = 'copy file or directory')
    copy.add_argument('src', help = 'path to copy from')
    copy.add_argument('dst', help = 'path to copy to')
    copy.add_argument('-stat', default = False, action = 'store_true', help = 'copy the permission bits, last access time, last modification time, and flags')
    copy.set_defaults(func = CopyCmd)

    delete = subparsers.add_parser('del', help = 'delete file or directory')
    delete.add_argument('src', help = 'path to delete')
    delete.add_argument('-sfx', nargs = '+', help = 'also delete path (src + suffix), useful for unity .meta files')
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
