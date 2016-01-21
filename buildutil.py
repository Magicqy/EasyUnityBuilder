#!/usr/bin/python

'''
utility for build and package Unity3D projects.

author:     Qu Yong <work.qu@outlook.com>
version:    0.5.0
'''

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

class Utility:
    @staticmethod
    def InitLogging(homePath, logFile, logFileMode, unityLogFile):
        import logging
        logger = logging.getLogger()
        for hd in logger.handlers:
            hd.close()
        del logger.handlers[:]
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.StreamHandler(sys.stdout))
        if logFile:
            logger.addHandler(logging.FileHandler(logFile, 'w' if logFileMode else 'a'))
            Utility.Log('===Initializing===')
            Utility.Log('datetime:  %s' %datetime.datetime.now())
            Utility.Log('logFile:   %s' %logFile)
        Utility.invokeLogFile = os.path.join(homePath, 'invoke.log')
        pass

    @staticmethod
    def Log(msg, exitWithCode = None):
        import logging
        logging.info(msg)
        if exitWithCode != None:
            logging.shutdown()
            sys.exit(exitWithCode)
        pass

    @staticmethod
    def FullPath(path):
        return os.path.abspath(os.path.expanduser(path)) if path else None

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
        return root + Utility.extSwitch[buildTarget](ext, buildOpts.find(BuildOptions.AcceptExternalModificationsToPlayer) < 0)
    pass

#util methods
def Setup(projPath, homePath):
    Copy(os.path.join(homePath, 'BuildUtility/BuildUtility.cs'), os.path.join(projPath, 'Assets/Editor/_BuildUtility_/BuildUtility.cs'))
    Copy(os.path.join(homePath, 'BuildUtility/Invoker/Invoker.cs'), os.path.join(projPath, 'Assets/Editor/_BuildUtility_/Invoker.cs'))
    pass

def Cleanup(projPath):
    Del(os.path.join(projPath, 'Assets/Editor/_BuildUtility_'), ['.meta'])
    path = Utility.invokeLogFile
    if path and os.path.exists(path):
        logFile = open(path)
        try:
            Utility.Log(logFile.read())
        finally:
            logFile.close()
            Del(path)
    pass

def Copy(src, dst, append = False, stat = False):
    if src == dst or src == None or not os.path.exists(src):
        Utility.Log('copy failed, %s >> %s' %(src, dst), 1)

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
        Utility.Log('path is not a file or directory: %s' %src)
    pass

def Del(path, alsoDelSuffixes = None):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        Utility.Log('path is not a file or directory: %s' %path)

    if alsoDelSuffixes:
        for suffix in alsoDelSuffixes:
            Del(path + suffix)
    pass

class Invoker:
    def __init__(self, methodName, argList):
        self.invokeList = ['-executeMethod', 'Invoker.Invoke', methodName]
        self.invokeList.extend(argList)
        pass

    def Append(self, methodName, argList):
        self.invokeList.append('-next')
        self.invokeList.append(methodName)
        self.invokeList.extend(argList)
        return self

    def Invoke(self, projPath, homePath, unityExe, unityLog, batch = True, quit = True):
        argList = [unityExe, '-projectPath', projPath]
        if unityLog:
            argList.extend(['-logFile', unityLog])
        if batch:
            argList.append('-batchmode')
        if quit:
            argList.append('-quit')
        if Utility.invokeLogFile:
            argList.extend(['-invokeLog', Utility.invokeLogFile])
        argList.extend(self.invokeList)

        Utility.Log('===Invoke===')
        Utility.Log('unityPath:       %s' %unityExe)
        Utility.Log('projectPath:     %s' %projPath)
        Utility.Log('unityLogPath:    %s' %unityLog)
        Utility.Log('batchmode:       %s' %batch)
        Utility.Log('quit:            %s' %quit)
        Utility.Log('')
        for i in range(2, len(self.invokeList)):
            Utility.Log(self.invokeList[i])
        Utility.Log('')
        
        if os.path.isdir(projPath):
            try:
                Setup(projPath, homePath)
                Utility.Log(' '.join(argList))
                ret = subprocess.call(argList)
                if ret != 0:
                    Utility.Log('execute fail with retcode: %s' %ret, ret)
                return ret
            finally:
                Cleanup(projPath)
        else:
            Utility.Log('projectPath not exist: %s' %projPath, 1)
    pass

def BuildCmd(args):
    projPath = Utility.FullPath(args.projPath)
    buildTarget = BuildTarget.From(args.buildTarget)
    buildOpts = BuildOptions.From(args.opt, args.exp, args.dev)
    outPath = Utility.CorrectExt(Utility.FullPath(args.outPath), buildTarget, buildOpts)

    #cleanup
    Del(outPath)
    if buildTarget == BuildTarget.StandaloneWindows or buildTarget == BuildTarget.StandaloneWindows64:
        Del(os.path.splitext(outPath)[0] + '_Data')

    dir = os.path.dirname(outPath)
    if not os.path.exists(dir):
        os.makedirs(dir)

    ivk = Invoker('BuildUtility.BuildPlayer', [outPath, buildTarget, buildOpts])
    ret = ivk.Invoke(projPath, args.homePath, args.unityExe, args.ulog, not args.nobatch, not args.noquit)
    
    #place exported project in outPath/ instead of outPath/productName/
    if ret == 0 and buildTarget == BuildTarget.Android and BuildOptions.AcceptExternalModifications(buildOpts) and not args.dph:
        for dir in os.listdir(outPath):
            expDir = os.path.join(outPath, dir)
            if os.path.isdir(expDir):
                Copy(expDir, outPath, True)
                Del(expDir)
                break
    pass

def InvokeCmd(args):
    projPath = Utility.FullPath(args.projPath)
    
    ivk = Invoker(args.methodName, args.args)
    if args.next:
        for nlist in args.next:
            ivk.Append(nlist[0], nlist[1:])
    ivk.Invoke(projPath, args.homePath, args.unityExe, args.ulog, not args.nobatch, not args.noquit)
    pass

def PackageAndroidCmd(args):
    projPath = Utility.FullPath(args.projPath)
    gradlePath = os.path.join(args.homePath, 'gradlew')
    buildFile = Utility.FullPath(args.bf) if args.bf else os.path.join(projPath, 'build.gradle')
    taskPrefix = args.pfx if args.pfx else ''
    taskSuffix = '%s%s' %(args.sfx[0].upper(), args.sfx[1:]) if args.sfx else ''

    argList = [os.path.join(gradlePath, 'gradlew.bat' if args.winOS else 'gradlew'), '-p', projPath, '-b', buildFile]
    if not args.ndp:
        argList.extend(['-P', 'targetProjDir=%s' %projPath,
                        '-P', 'buildDir=%s' %os.path.join(projPath, 'build'),
                        '-P', 'archivesBaseName=%s' %os.path.basename(projPath)])
    if args.prop:
        for item in args.prop:
            argList.append('-P')
            argList.append(item)
    
    if args.task:
        argList.extend(args.task)
    elif args.var:
        if args.pfx == None:
            if args.sfx == None:
                Utility.Log('execute task with variants but prefix and suffix are not found')
            for var in args.var:
                argList.append('%s%s%s' %(taskPrefix, var, taskSuffix))
        else:
            for var in args.var:
                argList.append('%s%s%s%s' %(taskPrefix, var[0].upper(), var[1:], taskSuffix))
    else:
        Utility.Log('no task to execute', 1)

    if not os.path.isdir(projPath):
        Utility.Log('project directory not exist: %s' %projPath, 1)
    if not os.path.isfile(buildFile):
        Utility.Log('build.gradle file not exist: %s' %buildFile, 1)

    Utility.Log('===Packge Android===')
    Utility.Log('projectPath:     %s' %projPath)
    Utility.Log('buildFile:       %s' %buildFile)
    Utility.Log('')

    try:
        Utility.Log(' '.join(argList))
        ret = subprocess.call(argList)
        if ret != 0:
            Utility.Log('execute gradle task failed with retcode: %s' %ret, ret)
    except:
        Utility.Log('package failed with excpetion', 1)
    pass

def PackageiOSCmd(args):
    if args.winOS != False:
        Utility.Log('package iOS only support on MacOS', 1)

    projPath = Utility.FullPath(args.projPath)
    buildType = 'Debug' if args.debug else 'Release'
    buildTarget = args.target
    buildSdk = str(args.sdk).lower()
    pkgOutFile = Utility.FullPath(args.outFile) if args.outFile else projPath + '.ipa'
    productName = args.proName
    provProfile = None
    if args.provFile:
        provFile = Utility.FullPath(args.provFile)
        if os.path.isfile(provFile):
            try:
                argList = ['security', 'cms', '-D', '-i', provFile]
                Utility.Log(' '.join(argList))
                provStr = subprocess.check_output(argList)
                prov = plistlib.readPlistFromString(provStr)
                provProfile = prov['UUID']
                if productName == None:
                    productName = prov['Entitlements']['application-identifier'].split('.')[-1]
            except:
                Utility.Log('get key values from provision file failed: %s' %provFile, 1)
        else:
            Utility.Log('provision file not exists: %s' %provFile, 1)

    if provProfile == None:
        Utility.Log('provision profile not found', 1)
    if not os.path.isdir(projPath):
        Utility.Log('project directory not exist: %s' %projPath, 1)

    Utility.Log('===Package iOS===')
    Utility.Log('projectPath:     %s' %projPath)
    Utility.Log('buildType:       %s' %buildType)
    Utility.Log('buildTarget:     %s' %buildTarget)
    Utility.Log('buildSdk:        %s' %buildSdk)
    Utility.Log('provision:       %s' %provProfile)
    Utility.Log('productName:     %s' %productName)
    Utility.Log('pkgOutFile:      %s' %pkgOutFile)
    Utility.Log('')

    #try resolve the 'User Interaction Is Not Allowed' problem when run from shell
    if args.keychain:
        argList = ['security', 'unlock-keychain', '-p', args.keychain[1], Utility.FullPath(args.keychain[0])]
        Utility.Log(' '.join(argList))
        ret = subprocess.call(argList)
        if ret != 0:
            Utility.Log('unlock keychain failed with retcode: %s' %ret)

    argList = ['xcodebuild',
               '-project', os.path.join(projPath, '%s.xcodeproj' %buildTarget),
               'clean',
               '-target', buildTarget,
               '-configuration', buildType]
    Utility.Log(' '.join(argList))
    ret = subprocess.call(argList)
    if ret != 0:
        Utility.Log('execute clean failed with retcode: %s' %ret, ret)

    argList = ['xcodebuild',
               '-project', os.path.join(projPath, '%s.xcodeproj' %buildTarget),
               '-sdk', buildSdk,
               '-target', buildTarget,
               '-configuration', buildType,
               'PROVISIONING_PROFILE=%s' %provProfile,
               'PRODUCT_NAME=%s' %productName]
    if not args.ndo:
        argList.extend(['DEPLOYMENT_POSTPROCESSING=YES',
                        'STRIP_INSTALLED_PRODUCT=YES',
                        'SEPARATE_STRIP=YES',
                        'COPY_PHASE_STRIP=YES'])
    if args.opt:
        argList.extend(args.opt)
    Utility.Log(' '.join(argList))
    ret = subprocess.call(argList)
    if ret != 0:
        Utility.Log('execute xcodebuild failed with retcode: %s' %ret, ret)
    
    #how to get archiveBaseName or bundle identifier?
    buildOutFile = os.path.join(projPath, 'build/%s-iphoneos/%s.app' %(buildType, productName))
    if not os.path.exists(buildOutFile):
        Utility.Log('build output file not exist: %s' %buildOutFile, 1)
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
    Utility.Log(' '.join(argList))
    ret = subprocess.call(argList)
    if ret != 0:
        Utility.Log('execute xcrun failed with retcode: %s' %ret, ret)
    pass

def CopyCmd(args):
    src = Utility.FullPath(args.src)
    dst = Utility.FullPath(args.dst)

    Utility.Log('===Copy===')
    Utility.Log('src:     %s' %src)
    Utility.Log('dst:     %s' %dst)
    Utility.Log('append:  %s' %args.append)
    Utility.Log('stat:    %s' %args.stat)

    Copy(src, dst, args.append, args.stat)
    pass

def DelCmd(args):
    path = Utility.FullPath(args.src)

    Utility.Log('===Delete===')
    Utility.Log('path:    %s' %path)
    if args.sfx:
        for suffix in args.sfx:
            Utility.Log('path:    %s%s' %(path, suffix))
    
    Del(path, args.sfx)
    pass

def Run(args):
    #workspace home
    args.homePath = os.path.dirname(sys.argv[0])

    #initialize logging
    args.ulog = Utility.FullPath(args.ulog)
    args.log = Utility.FullPath(args.log) 
    if args.log:
        dir = os.path.dirname(args.log)
        if not os.path.exists(dir):
            os.makedirs(dir)
    Utility.InitLogging(args.homePath, args.log, args.wmode, args.ulog)

    #unity home and executable
    args.unity = Utility.FullPath(args.unity) if args.unity else os.environ.get('UNITY_HOME')
    if args.unity and os.path.exists(args.unity):
        if sys.platform.startswith('win32'):
            args.winOS = True
            args.unityExe = os.path.join(args.unity, 'Unity.exe')
        elif sys.platform.startswith('darwin'):
            args.winOS = False
            args.unityExe = os.path.join(args.unity, 'Unity.app/Contents/MacOS/Unity')
        else:
            Utility.Log('Unsupported platform: %s' %sys.platform, 1)
        
        if args.unityExe == None or os.path.exists(args.unityExe) == False:
            Utility.Log('Unity executable not found at: %s' %args.unityExe, 1)
    else:
        Utility.Log('Unity home path not found, use -unity argument or define it with an environment variable UNITY_HOME', 1)

    args.func(args)
    pass

#parse arguments
def ParseArgs(explicitArgs = None):
    parser = argparse.ArgumentParser(description = 'build util for Unity')
    parser.add_argument('-log', help = 'build util log file path')
    parser.add_argument('-wmode', action = 'store_true', help = 'use w mode to open log file, by default the mode is a')
    parser.add_argument('-unity', help = 'unity home path')
    parser.add_argument('-ulog', help = 'unity editor log file path')
    parser.add_argument('-nobatch', action = 'store_true', help = 'run unity without -batchmode')
    parser.add_argument('-noquit', action = 'store_true', help = 'run unity without -quit')

    subparsers = parser.add_subparsers(help = 'sub-command list')
    invoke = subparsers.add_parser('invoke', help = 'invoke method with arguments')
    invoke.add_argument('projPath', help = 'target unity project path')
    invoke.add_argument('methodName',
                        help = 'method name to invoke, [Assembly:(Optional)]Namespace.SubNamespace.Class+NestedClass.Method')
    invoke.add_argument('args', nargs = '*', help = 'method arguments, support types: primitive / string / enum')
    invoke.add_argument('-next', action = 'append', nargs = '+', help = 'next method and arguments to invoke')
    invoke.set_defaults(func = InvokeCmd)

    build = subparsers.add_parser('build', help='build player for unity project')
    build.add_argument('projPath', help = 'target unity project path')
    build.add_argument('buildTarget', choices = ['android', 'ios', 'win', 'win64', 'osx', 'osx64'],
                       help = 'build target type')
    build.add_argument('outPath', help = 'build output path')
    build.add_argument('-opt', help = 'build options, see UnityEditor.BuildOptions for detail')
    build.add_argument('-exp', action = 'store_true', help = 'export project but not build it (android and ios only)')
    build.add_argument('-dev', action = 'store_true', help = 'enable unity development build, with debug symbols and internal profiler')
    build.add_argument('-dph', action = 'store_true',
                       help = 'unity export android project to outPath/{productName}/{exportProj} by default, without this option, project will be export to outPath/{exportProj}')
    build.set_defaults(func = BuildCmd)

    packandroid = subparsers.add_parser('packandroid', help = 'pacakge android project with gralde')
    packandroid.add_argument('projPath', help = 'target project path')
    packandroid.add_argument('-bf', help = 'specifies the build file')
    group = packandroid.add_mutually_exclusive_group(required = True)
    group.add_argument('-task', nargs = '+', help = 'full task names to execute')
    group.add_argument('-var', nargs = '+',
                       help = 'works together with task name prefix and suffix, the same as task {prefix}{Variant}{Suffix}')
    packandroid.add_argument('-pfx', help = 'task name prefix')
    packandroid.add_argument('-sfx', help = 'task name suffix')
    packandroid.add_argument('-prop', nargs = '*',
                             help = '''additional gradle build properties,
                             targetProjDir={projPath}, buildDir={projPath/build}, archivesBaseName={dirName(projPath)} by default''')
    packandroid.add_argument('-ndp', action = 'store_true', help = 'does not add default build properties')
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
                     check https://developer.apple.com/library/mac/documentation/DeveloperTools/Reference/XcodeBuildSettingRef for more information''')
    packios.add_argument('-ndo', action = 'store_true', help = 'does not add default build options')
    packios.set_defaults(func = PackageiOSCmd)

    copy = subparsers.add_parser('copy', help = 'copy file or directory')
    copy.add_argument('src', help = 'path to copy from')
    copy.add_argument('dst', help = 'path to copy to')
    copy.add_argument('-append', default = False, action = 'store_true',
                      help = 'append files from src to dst instead of delete dst before copy, only take effect when copy directory')
    copy.add_argument('-stat', default = False, action = 'store_true',
                      help = 'copy the permission bits, last access time, last modification time, and flags')
    copy.set_defaults(func = CopyCmd)

    delete = subparsers.add_parser('del', help = 'delete file or directory')
    delete.add_argument('src', help = 'path to delete')
    delete.add_argument('-sfx', nargs = '*', help = 'also delete path (src + suffix), useful for unity .meta files')
    delete.set_defaults(func = DelCmd)

    return parser.parse_args(explicitArgs)
    pass

#script interface
INVOKE = 'invoke'
BUILD = 'build'
PACK_ANDROID = 'packandroid'
PACK_IOS = 'packios'
COPY = 'copy'
DEL = 'del'

def runTask(task, mapargs, **kwargs):
    '''
    argument names
    common:         log, wmode, ulog, unity, nobatch, noquit
    invoke:         projPath, calls
    build:          projPath, buildTarget, outPath, opt, exp, dev, dph
    packandroid:    projPath, bf, task, var, pfx, sfx, prop, ndp
    packios:        projPath, provFile, outFile, proName, debug, target, sdk, keychain, opt, ndo
    copy:           src, dst, append, stat
    del:            src, sfx
    '''
    parser = _argparser(mapargs, cmd = task)
    parser.update(kwargs)
    explictArgs = parser.parse()
    Run(ParseArgs(explictArgs))

class _argparser(dict):
    def parse(self):
        cmd = self.__common()
        if cmd == INVOKE:
            self.__invoke()
        elif cmd == BUILD:
            self.__build()
        elif cmd == PACK_ANDROID:
            self.__packandroid()
        elif cmd == PACK_IOS:
            self.__packios()
        elif cmd == COPY:
            self.__copy()
        elif cmd == DEL:
            self.__del()
        return self.__arglist

    def __common(self):
        self.__appends('-log', self.log)
        self.__appendb('-wmode', self.wmode)
        self.__appends('-unity', self.unity)
        self.__appends('-ulog', self.ulog)
        self.__appendb('-nobatch', self.nobatch)
        self.__appendb('-noquit', self.noquit)
        return self.cmd

    def __invoke(self):
        self.__append(self.cmd)
        self.__append(self.projPath)
        calls = self.calls
        if calls:
            isfirst = True
            for c in calls:
                if isfirst:
                    isfirst = False
                else:
                    self.__append('-next')
                self.__extend(c)

    def __build(self):
        self.__append(self.cmd)
        self.__append(self.projPath)
        self.__append(self.buildTarget)
        self.__append(self.outPath)
        self.__appends('-opt', self.opt)
        self.__appendb('-exp', self.exp)
        self.__appendb('-dev', self.dev)
        self.__appendb('-dph', self.dph)

    def __packandroid(self):
        self.__append(self.cmd)
        self.__append(self.projPath)
        self.__appends('-bf', self.bf)
        if self.task:
            self.__appends('-task', self.task)
        elif self.var:
            self.__appends('-var', self.var)
            self.__appends('-pfx', self.pfx)
            self.__appends('-sfx', self.sfx)
        self.__appends('-prop', self.prop)
        self.__appendb('-ndp', self.ndp)

    def __packios(self):
        self.__append(self.cmd)
        self.__append(self.projPath)
        self.__appends('-provFile', self.provFile)
        self.__appends('-outFile', self.outFile)
        self.__appends('-proName', self.proName)
        self.__appendb('-debug', self.debug)
        self.__appends('-target', self.target)
        self.__appends('-sdk', self.sdk)
        self.__appends('-keychain', self.keychain)
        self.__appends('-opt', self.opt)
        self.__appends('-ndo', self.ndo)

    def __copy(self):
        self.__append(self.src)
        self.__append(self.dst)
        self.__appendb('-append', self.append)
        self.__appendb('-stat', self.stat)

    def __del(self):
        self.__append(self.src)
        self.__appends('-sfx', self.sfx)

    def __init__(self, o, **kwargs):
        self.__arglist = []
        if o:
            return super(_argparser, self).__init__(o, **kwargs)
        else:
            return super(_argparser, self).__init__(kwargs)

    def __getattr__(self, arg):
        return self[arg] if arg in self else None

    def __append(self, arg):
        if arg: self.__arglist.append(arg)

    def __extend(self, args):
        if args: self.__arglist.extend(args)

    def __appends(self, k, v):
        if k and v:
            self.__append(k)
            if isinstance(v, list):
                self.__extend(v)
            else:
                self.__append(v)

    def __appendb(self, k, v):
        if k and v:
            self.__append(k)
    pass

if __name__ == '__main__':
    Run(ParseArgs())
    pass
