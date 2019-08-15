#!/usr/bin/python

'''
utility for build and package Unity3D projects.

author:     Qu Yong <work.qu@outlook.com>
version:    0.5.0
'''

import os, sys, shutil, datetime, argparse, subprocess, plistlib

#util methods
class _BuildTarget:
    Android = 'Android'
    iOS = 'iOS'
    StandaloneWindows = 'StandaloneWindows'
    StandaloneWindows64 = 'StandaloneWindows64'
    StandaloneOSXIntel = 'StandaloneOSXIntel'
    StandaloneOSXIntel64 = 'StandaloneOSXIntel64'
    
    _switch = {
        'android' : Android,
        'ios' : iOS,
        'win' : StandaloneWindows,
        'win64' : StandaloneWindows64,
        'osx' : StandaloneOSXIntel,
        'osx64' : StandaloneOSXIntel64,
        }

    @staticmethod
    def From(targetStr):
        return _BuildTarget._switch[targetStr]
    pass

class _BuildOptions:
    AcceptExternalModificationsToPlayer = 'AcceptExternalModificationsToPlayer'
    Development = 'Development'

    @staticmethod
    def From(opt, exp, dev):
        bo = str(opt)
        if exp:
            bo = '%s|%s' %(bo, _BuildOptions.AcceptExternalModificationsToPlayer)
        if dev:
            bo = '%s|%s' %(bo, _BuildOptions.Development)
        return bo

    @staticmethod
    def AcceptExternalModifications(buildOpts):
        return buildOpts.find(_BuildOptions.AcceptExternalModificationsToPlayer) >= 0
    pass

def _initLogging(homePath, logFile, logFileMode):
    import logging
    logger = logging.getLogger()
    for hd in logger.handlers:
        hd.close()
    del logger.handlers[:]
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    if logFile:
        logger.addHandler(logging.FileHandler(logFile, 'w' if logFileMode else 'a'))
        _logInfo('===Initializing===')
        _logInfo('datetime:  %s' %datetime.datetime.now())
        _logInfo('logFile:   %s' %logFile)
    pass

def _logInfo(msg, exitWithCode = None):
    import logging
    logging.info(msg)
    if exitWithCode != None:
        logging.shutdown()
        sys.exit(exitWithCode)
    pass

def _fullPath(path):
    return os.path.abspath(os.path.expanduser(path)) if path else None

def _correctExt(outPath, buildTarget, buildOpts):
    root, ext = os.path.splitext(outPath)
    noexp = buildOpts.find(_BuildOptions.AcceptExternalModificationsToPlayer) < 0
    if buildTarget == _BuildTarget.Android:
        return root + '.apk' if noexp and len(ext) == 0 else outPath
    elif buildTarget == _BuildTarget.iOS:
        return outPath
    elif buildTarget == _BuildTarget.StandaloneWindows or ext == _BuildTarget.StandaloneWindows64:
        return root + '/bin.exe' if len(ext) == 0 else outPath
    elif buildTarget == _BuildTarget.StandaloneOSXIntel or ext == _BuildTarget.StandaloneOSXIntel64:
        return root + '.app' if len(ext) == 0 else outPath
    else:
        _logInfo('invalid build target:%s' %buildTarget)
        return root + ext
    pass

def _copy(src, dst, append = False, stat = False):
    if src == dst or src == None or not os.path.exists(src):
        _logInfo('copy failed, %s >> %s' %(src, dst), 1)

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
            _copy(srcPath, dstPath, append, stat)
    elif os.path.isfile(src):
        #src and dst are files
        if os.path.exists(dst):
            _del(dst)
        else:
            dstDir = os.path.dirname(dst)
            if not os.path.exists(dstDir):
                os.makedirs(dstDir)

        shutil.copyfile(src, dst)
        if stat:
            shutil.copystat(src, dst)
    else:
        _logInfo('path is not a file or directory: %s' %src)
    pass

def _del(path, alsoDelSuffixes = None):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        _logInfo('path is not a file or directory: %s' %path)

    if alsoDelSuffixes:
        for suffix in alsoDelSuffixes:
            _del(path + suffix)
    pass

class _Invoker:
    def __init__(self, methodName, argList):
        self.invokeList = ['-executeMethod', 'Invoker.InvokeCommandLine', methodName]
        self.invokeList.extend(argList)
        pass

    def append(self, methodName, argList):
        self.invokeList.append('-next')
        self.invokeList.append(methodName)
        self.invokeList.extend(argList)
        return self

    def invoke(self, projPath, args):
        homePath = args.homePath
        unityExe = args.unityExe
        unityLog = args.unityLog
        switchTarget = args.switchTarget
        batchmode = not args.nobatch
        quit = not args.noquit

        argList = [unityExe]
        if unityLog:
            argList.extend(['-logFile', unityLog])
        if switchTarget:
            argList.extend(['-buildTarget', switchTarget])
        if batchmode:
            argList.append('-batchmode')
        if quit:
            argList.append('-quit')
        if projPath:
            argList.extend(['-projectPath', projPath])

        self.invokeLogFile = os.path.join(projPath, 'invoke.log')
        argList.extend(['-invokeLog', self.invokeLogFile])
        argList.extend(self.invokeList)

        _logInfo('===Invoke===')
        _logInfo('unityExePath:    %s' %unityExe)
        _logInfo('unityLogPath:    %s' %unityLog)
        _logInfo('switchTarget:    %s' %switchTarget)
        _logInfo('batchmode:       %s' %batchmode)
        _logInfo('quit:            %s' %quit)
        _logInfo('projectPath:     %s' %projPath)
        _logInfo('')
        for i in range(2, len(self.invokeList)):
            _logInfo(self.invokeList[i])
        _logInfo('')
        
        if os.path.isdir(projPath):
            try:
                self._setup(projPath, homePath)
                _logInfo(' '.join(argList))
                ret = subprocess.call(argList)
                if ret != 0:
                    _logInfo('execute fail with retcode: %s' %ret, ret)
                return ret
            finally:
                self._cleanup(projPath)
        else:
            _logInfo('projectPath not exist: %s' %projPath, 1)
        pass
         
    def _setup(self, projPath, homePath):
        #try avoid path conflict with prefix
        _copy(os.path.join(homePath, 'EditorScripts/BuildUtility.cs'),
              os.path.join(projPath, 'Assets/_UnityBuildUtility/Editor/BuildUtility.cs'))
        _copy(os.path.join(homePath, 'EditorScripts/Invoker.cs'),
              os.path.join(projPath, 'Assets/_UnityBuildUtility/Editor/Invoker.cs'))
        pass

    def _cleanup(self, projPath):
        _del(os.path.join(projPath, 'Assets/_UnityBuildUtility'), ['.meta'])
        path = self.invokeLogFile
        if path and os.path.exists(path):
            logFile = open(path)
            try:
                _logInfo(logFile.read())
            finally:
                logFile.close()
                _del(path)
        pass
    pass

def _buildCmd(args):
    #check unity home and executable
    args.unityHome = _fullPath(args.unityHome) if args.unityHome else os.environ.get('UNITY_HOME')
    if args.unityHome and os.path.exists(args.unityHome):
        if args.winOS:
            args.unityExe = os.path.join(args.unityHome, 'Unity.exe')
        else:
            args.unityExe = os.path.join(args.unityHome, 'Unity.app/Contents/MacOS/Unity')

        if os.path.exists(args.unityExe) == False:
            _logInfo('Unity executable not found at: %s' %args.unityExe, 1)
    else:
        _logInfo('Unity home path not found, use -unityHome argument or define it with an environment variable UNITY_HOME', 1)

    projPath = _fullPath(args.projPath)
    buildTarget = _BuildTarget.From(args.buildTarget)
    buildOpts = _BuildOptions.From(args.opt, args.exp, args.dev)
    outPath = _correctExt(_fullPath(args.outPath), buildTarget, buildOpts)

    #cleanup
    _del(outPath)
    if buildTarget == _BuildTarget.StandaloneWindows or buildTarget == _BuildTarget.StandaloneWindows64:
        _del(os.path.splitext(outPath)[0] + '_Data')

    dir = os.path.dirname(outPath)
    if not os.path.exists(dir):
        os.makedirs(dir)

    ivk = _Invoker('_BuildUtility.BuildPlayer', [outPath, buildTarget, buildOpts])
    ret = ivk.invoke(projPath, args)
    
    #place exported project in outPath/ instead of outPath/productName/
    if ret == 0 and buildTarget == _BuildTarget.Android and _BuildOptions.AcceptExternalModifications(buildOpts) and not args.dph:
        for dir in os.listdir(outPath):
            expDir = os.path.join(outPath, dir)
            if os.path.isdir(expDir):
                _copy(expDir, outPath, True)
                _del(expDir)
                break
    pass

def _invokeCmd(args):
    #check unity home and executable
    args.unityHome = _fullPath(args.unityHome) if args.unityHome else os.environ.get('UNITY_HOME')
    if args.unityHome and os.path.exists(args.unityHome):
        if args.winOS:
            args.unityExe = os.path.join(args.unityHome, 'Unity.exe')
        else:
            args.unityExe = os.path.join(args.unityHome, 'Unity.app/Contents/MacOS/Unity')

        if os.path.exists(args.unityExe) == False:
            _logInfo('Unity executable not found at: %s' %args.unityExe, 1)
    else:
        _logInfo('Unity home path not found, use -unityHome argument or define it with an environment variable UNITY_HOME', 1)

    projPath = _fullPath(args.projPath)
    ivk = _Invoker(args.methodName, args.args)
    if args.next:
        for nlist in args.next:
            ivk.append(nlist[0], nlist[1:])
    ivk.invoke(projPath, args)
    pass

def _packageAndroidCmd(args):
    projPath = _fullPath(args.projPath)
    gradlePath = os.path.join(args.homePath, 'gradlew')
    buildFile = _fullPath(args.buildFile) if args.buildFile else os.path.join(projPath, 'build.gradle')
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
                _logInfo('execute task with variants but prefix and suffix are not found')
            for var in args.var:
                argList.append('%s%s%s' %(taskPrefix, var, taskSuffix))
        else:
            for var in args.var:
                argList.append('%s%s%s%s' %(taskPrefix, var[0].upper(), var[1:], taskSuffix))
    else:
        _logInfo('no task to execute', 1)

    if not os.path.isdir(projPath):
        _logInfo('project directory not exist: %s' %projPath, 1)
    if not os.path.isfile(buildFile):
        _logInfo('build.gradle file not exist: %s' %buildFile, 1)

    _logInfo('===Packge Android===')
    _logInfo('projectPath:     %s' %projPath)
    _logInfo('buildFile:       %s' %buildFile)
    _logInfo('')

    try:
        _logInfo(' '.join(argList))
        ret = subprocess.call(argList)
        if ret != 0:
            _logInfo('execute gradle task failed with retcode: %s' %ret, ret)
    except:
        _logInfo('package failed with excpetion', 1)
    pass

def _packageiOSCmd(args):
    if args.winOS != False:
        _logInfo('package iOS only support on MacOS', 1)

    projPath = _fullPath(args.projPath)
    buildConfig = 'Debug' if args.debug else 'Release'
    buildTarget = args.target
    buildSdk = str(args.sdk).lower()
    pkgOutFile = _fullPath(args.outFile) if args.outFile else projPath + '.ipa'
    productName = args.proName
    teamId = None
    teamName = None
    bundleId = None
    provName = None
    provUUID = None
    provType = None
    if args.provFile:
        provFile = _fullPath(args.provFile)
        if os.path.isfile(provFile):
            try:
                argList = ['security', 'cms', '-D', '-i', provFile]
                _logInfo(' '.join(argList))
                provStr = subprocess.check_output(argList)
                provObj = plistlib.readPlistFromString(provStr)

                #these key names may change when Apple update the plist format of mobileprovision file
                #enterprise,    valid for all devices, distribution profile
                #app-store,     valid only for upload to appstore, distribution profile
                #development,   valid for limited devices, development profile
                #ad-hoc,        valid for limited devices, distribution profile 
                validForAll = provObj.get('ProvisionsAllDevices')
                validForLimited = provObj.get('ProvisionedDevices')
                if validForAll:
                    provType = 'enterprise'
                elif validForLimited:
                    provType = 'development'
                    #TODO how to recognize ad-hoc profile?
                else:
                    provType = 'app-store'

                teamId = provObj['Entitlements']['com.apple.developer.team-identifier']
                teamName = 'iPhone Developer: ' if provType == 'development' else 'iPhone Distribution: ' + provObj['TeamName']
                bundleId = provObj['Entitlements']['application-identifier'][len(teamId) + 1:]
                provName = provObj['Name']
                provUUID = provObj['UUID']
                if productName == None:
                    productName = provObj['Entitlements']['application-identifier'].split('.')[-1]
            except:
                _logInfo('get key values from provision file failed: %s' %provFile, 1)
        else:
            _logInfo('provision file not exists: %s' %provFile, 1)

    if provUUID == None:
        _logInfo('provision profile not found', 1)
    if not os.path.isdir(projPath):
        _logInfo('project directory not exist: %s' %projPath, 1)

    _logInfo('===Package iOS===')
    _logInfo('projectPath:          %s' %projPath)
    _logInfo('buildConfiguration:   %s' %buildConfig)
    _logInfo('buildTarget:          %s' %buildTarget)
    _logInfo('buildSdk:             %s' %buildSdk)
    _logInfo('bundleId:             %s' %bundleId)
    _logInfo('provision name:       %s' %provName)
    _logInfo('provision uuid:       %s' %provUUID)
    _logInfo('productName:          %s' %productName)
    _logInfo('pkgOutFile:           %s' %pkgOutFile)
    _logInfo('')

    #try resolve the 'User Interaction Is Not Allowed' problem when run from shell
    #need build manully once and click 'Always Allow' on the keychain unlock confirm dialog
    #when your project takes a very long time to build, increase auto-lock duration on keychain settings
    if args.keychain:
        argList = ['security', 'unlock-keychain', '-p', args.keychain[1], _fullPath(args.keychain[0])]
        _logInfo(' '.join(argList))
        ret = subprocess.call(argList)
        if ret != 0:
            _logInfo('unlock keychain failed with retcode: %s' %ret)

    argList = ['xcodebuild',
               '-project', os.path.join(projPath, '%s.xcodeproj' %buildTarget),
               '-target', buildTarget,
               '-configuration', buildConfig,
               'clean']
    _logInfo(' '.join(argList))
    ret = subprocess.call(argList)
    if ret != 0:
        _logInfo('execute clean failed with retcode: %s' %ret, ret)

    archiveOutPath = os.path.join(projPath, 'build/%s.xcarchive' %buildTarget)
    #the default name of scheme should be the same as build target
    buildScheme = buildTarget
    argList = ['xcodebuild',
               '-project', os.path.join(projPath, '%s.xcodeproj' %buildTarget),
               '-sdk', buildSdk,
               '-scheme', buildScheme,
               '-configuration', buildConfig,
               'PROVISIONING_PROFILE=%s' %provUUID,
               'CODE_SIGN_IDENTITY=%s' %teamName,
               'PRODUCT_NAME=%s' %productName]
    if not args.ndo:
        argList.extend(['DEPLOYMENT_POSTPROCESSING=YES',
                        'STRIP_INSTALLED_PRODUCT=YES',
                        'SEPARATE_STRIP=YES',
                        'COPY_PHASE_STRIP=YES'])
    argList.extend(['archive', '-archivePath', archiveOutPath])

    if args.opt:
        argList.extend(args.opt)
    _logInfo(' '.join(argList))
    ret = subprocess.call(argList)
    if ret != 0:
        _logInfo('execute xcodebuild failed with retcode: %s' %ret, ret)
    #check if build succeed
    if not os.path.exists(archiveOutPath):
        _logInfo('xcodebuild archive output file not exist: %s' %archiveOutPath, 1)

    exportOptFilePath = os.path.join(os.path.dirname(archiveOutPath), '%s.plist' %buildTarget)
    try:
        optFile = open(exportOptFilePath, 'w+')
        optFile.write("""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>method</key>
        <string>%s</string>
        <key>teamID</key>
        <string>%s</string>
        <key>compileBitcode</key>
        <false/>
        <key>signingCertificate</key>
        <string>%s</string>
        <key>provisioningProfiles</key>
        <dict>
            <key>%s</key>
            <string>%s</string>
            <key>uploadSymbols</key>
            <false/>
        </dict>
    </dict>
</plist>
""" %(provType, teamId, teamName, bundleId, provName))
        optFile.close()
    except:
        _logInfo('create exportOptionsPlist failed', 1)

    exportPath = os.path.dirname(archiveOutPath)
    argList = ['xcodebuild',
               '-exportArchive',
               '-archivePath', archiveOutPath,
               '-exportPath', exportPath,
               '-configuration', buildConfig,
               '-exportOptionsPlist', exportOptFilePath]

    _logInfo(' '.join(argList))
    ret = subprocess.call(argList)
    if ret != 0:
        _logInfo('execute xcrun failed with retcode: %s' %ret, ret)
    pass
    #check if export package succeed
    pkgSrcFile = os.path.join(exportPath, "%s.ipa" %buildTarget)
    if os.path.exists(pkgSrcFile):
        _copy(pkgSrcFile, pkgOutFile)
        _del(pkgSrcFile)
    else:
        _logInfo('exported package file not exist: %s' %pkgSrcFile, 1)

    #exoprt archive files
    if args.archiveFile:
        archiveSrcFile = os.path.join(exportPath, "%s.xcarchive" %buildTarget)
        archiveOutFile = _fullPath(args.archiveFile)
        if os.path.exists(archiveSrcFile):
            _copy(archiveSrcFile, archiveOutFile)
            _del(archiveSrcFile)
        else:
            _logInfo('exported archive file not exist: %s' %archiveFile, 1)

def _copyCmd(args):
    src = _fullPath(args.src)
    dst = _fullPath(args.dst)

    _logInfo('===Copy===')
    _logInfo('src:     %s' %src)
    _logInfo('dst:     %s' %dst)
    _logInfo('append:  %s' %args.append)
    _logInfo('stat:    %s' %args.stat)

    _copy(src, dst, args.append, args.stat)
    pass

def _delCmd(args):
    path = _fullPath(args.src)

    _logInfo('===Delete===')
    _logInfo('path:    %s' %path)
    if args.sfx:
        for suffix in args.sfx:
            _logInfo('path:    %s%s' %(path, suffix))
    
    _del(path, args.sfx)
    pass

#commandline argument parse
def _parse_args(explicitArgs = None):
    parser = argparse.ArgumentParser(description = 'build util for Unity')
    parser.add_argument('-log', help = 'build util log file path')
    parser.add_argument('-wmode', action = 'store_true', help = 'use w mode to open log file, by default the mode is a')
    parser.add_argument('-unityHome', help = 'unity home path')
    parser.add_argument('-unityLog', help = 'unity editor log file path')
    parser.add_argument('-switchTarget', choices = ['Android', 'iOS', 'Win', 'Win64', 'OSXUniversal'],
        help = 'switch active build target before loading project')
    parser.add_argument('-nobatch', action = 'store_true', help = 'run unity without -batchmode')
    parser.add_argument('-noquit', action = 'store_true', help = 'run unity without -quit')

    subparsers = parser.add_subparsers(help = 'sub-command list')
    invoke = subparsers.add_parser('invoke', help = 'invoke method with arguments')
    invoke.add_argument('projPath', help = 'target unity project path')
    invoke.add_argument('methodName',
                        help = 'method name to invoke, [Assembly:(Optional)]Namespace.SubNamespace.Class+NestedClass.Method')
    invoke.add_argument('args', nargs = '*', help = 'method arguments, support types: primitive / string / enum')
    invoke.add_argument('-next', action = 'append', nargs = '+', help = 'next method and arguments to invoke')
    invoke.set_defaults(func = _invokeCmd)

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
    build.set_defaults(func = _buildCmd)

    packandroid = subparsers.add_parser('packandroid', help = 'pacakge android project with gralde')
    packandroid.add_argument('projPath', help = 'target project path')
    packandroid.add_argument('-buildFile', help = 'specifies the build file')
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
    packandroid.set_defaults(func = _packageAndroidCmd)

    packios = subparsers.add_parser('packios', help = 'pacakge iOS project with xCode')
    packios.add_argument('projPath', help = 'target project path')
    packios.add_argument('-provFile', help = 'path of the .mobileprovision file', required = True)
    packios.add_argument('-outFile', help = 'package file output path')
    packios.add_argument('-archiveFile', help = 'archive output path, for package and dsym files backup')
    packios.add_argument('-proName', help = 'specifies the product name')
    packios.add_argument('-debug', action = 'store_true', help = 'use Debug or Release build configuration')
    packios.add_argument('-target', default = 'Unity-iPhone', help = 'build target, Unity-iPhone by default')
    packios.add_argument('-sdk', default = 'iphoneos', help = 'build sdk version, latest iphoneos by default')
    packios.add_argument('-keychain', nargs = 2,
                     help = '''keychain path and passowrd.
                     unlock keychain before build (usually ~/Library/Keychains/login.keychain) to workaround for "User Interaction Is Not Allowed" problem.
                     click 'Always Allow' button at first time it ask for keychain access''')
    packios.add_argument('-opt', nargs = '*',
                     help = '''additional build options.
                     PRODUCT_NAME={proName} DEPLOYMENT_POSTPROCESSING=YES, STRIP_INSTALLED_PRODUCT=YES, SEPARATE_STRIP=YES, COPY_PHASE_STRIP=YES by default.
                     check https://developer.apple.com/library/mac/documentation/DeveloperTools/Reference/XcodeBuildSettingRef for more information''')
    packios.add_argument('-ndo', action = 'store_true', help = 'does not add default build options')
    packios.set_defaults(func = _packageiOSCmd)

    copy = subparsers.add_parser('copy', help = 'copy file or directory')
    copy.add_argument('src', help = 'path to copy from')
    copy.add_argument('dst', help = 'path to copy to')
    copy.add_argument('-append', default = False, action = 'store_true',
                      help = 'append files from src to dst instead of delete dst before copy, only take effect when copy directory')
    copy.add_argument('-stat', default = False, action = 'store_true',
                      help = 'copy the permission bits, last access time, last modification time, and flags')
    copy.set_defaults(func = _copyCmd)

    delete = subparsers.add_parser('del', help = 'delete file or directory')
    delete.add_argument('src', help = 'path to delete')
    delete.add_argument('-sfx', nargs = '*', help = 'also delete path (src + suffix), useful for unity .meta files')
    delete.set_defaults(func = _delCmd)

    return parser.parse_args(explicitArgs)
    pass

def _run(args):
    #workspace home
    args.homePath = os.path.dirname(sys.argv[0])

    #initialize logging
    args.unityLog = _fullPath(args.unityLog)
    args.log = _fullPath(args.log) 
    if args.log:
        dir = os.path.dirname(args.log)
        if not os.path.exists(dir):
            os.makedirs(dir)
    _initLogging(args.homePath, args.log, args.wmode)

    #system environment
    if sys.platform.startswith('win32'):
        args.winOS = True
    elif sys.platform.startswith('darwin'):
        args.winOS = False
    else:
        _logInfo('Unsupported platform: %s' %sys.platform, 1)

    args.func(args)
    pass

#script interface
INVOKE = 'invoke'
BUILD = 'build'
PACK_ANDROID = 'packandroid'
PACK_IOS = 'packios'
COPY = 'copy'
DEL = 'del'

class _ScriptTaskArgParser(dict):
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
        self.__appends('-unityHome', self.unityHome)
        self.__appends('-unityLog', self.unityLog)
        self.__appends('-switchTarget', self.switchTarget)
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
        self.__appends('-buildFile', self.buildFile)
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
        self.__appends('-archiveFile', self.archiveFile)
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
            return super(_ScriptTaskArgParser, self).__init__(o, **kwargs)
        else:
            return super(_ScriptTaskArgParser, self).__init__(kwargs)

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

def runTask(taskName, shared_args, **kwargs):
    '''
    task list:
    INVOKE, BUILD, PACK_ANDROID, PACK_IOS, COPY, DEL

    argument name list:
    shared:         log, wmode, unityHome, unityLog, switchTarget, nobatch, noquit
    invoke:         projPath, calls
    build:          projPath, buildTarget, outPath, opt, exp, dev, dph
    packandroid:    projPath, buildFile, task, var, pfx, sfx, prop, ndp
    packios:        projPath, provFile, outFile, archiveFile, proName, debug, target, sdk, keychain, opt, ndo
    copy:           src, dst, append, stat
    del:            src, sfx
    '''
    parser = _ScriptTaskArgParser(shared_args, cmd = taskName)
    parser.update(kwargs)
    explictArgs = parser.parse()
    _run(_parse_args(explictArgs))
    pass

if __name__ == '__main__':
    _run(_parse_args())
    pass
