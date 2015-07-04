using UnityEngine;
using UnityEditor;
using System.Collections;
using System.Collections.Generic;
using System.IO;

public static class BuildUtility
{
    public static void DelSymbolForGroup(BuildTargetGroup group, string symbol)
    {
        var defines = PlayerSettings.GetScriptingDefineSymbolsForGroup(group);
        var symbols = string.IsNullOrEmpty(defines) ? new List<string>() : new List<string>(defines.Split(';'));
        symbols.Remove(symbol);
        PlayerSettings.SetScriptingDefineSymbolsForGroup(group, string.Join(";", symbols.ToArray()));
    }

    public static void AddSymbolForGroup(BuildTargetGroup group, string symbol)
    {
        var defines = PlayerSettings.GetScriptingDefineSymbolsForGroup(group);
        var symbols = string.IsNullOrEmpty(defines) ? new List<string>() : new List<string>(defines.Split(';'));
        if (!symbols.Contains(symbol))
        {
            symbols.Add(symbol);
        }
        PlayerSettings.SetScriptingDefineSymbolsForGroup(group, string.Join(";", symbols.ToArray()));
    }

    public static void BuildPlayer(string outPath, BuildTarget target, BuildOptions opt)
    {
        List<string> levels = new List<string>();
        foreach (var s in EditorBuildSettings.scenes)
        {
            if (s.enabled)
                levels.Add(s.path);
        }
        if (levels.Count > 0)
        {
            var error = BuildPipeline.BuildPlayer(levels.ToArray(), outPath, target, opt);
            if (!string.IsNullOrEmpty(error))
            {
                Debug.LogError(error);
                EditorApplication.Exit(1);
            }
        }
        else
        {
            Debug.LogError("There is no enabled scene found in build settings");
            EditorApplication.Exit(1);
        }
    }

    public enum OptName
    {
        Identifier,
        VerCode,
        VerName,
        DevBuild,
        BuildTarget,
        ScriptSymbols,
        OutPath,
    }

    const string ARG_NAME = "-cmdbuild";
    const char OPT_SEP = ',';
    const char OPT_KV_SEP = '=';

    public static System.Action BuildPreprocess;
    public static System.Action BuildPostprocess;

    static readonly string BuildRevFilePath = Path.Combine(Application.dataPath, "Resources/BuildRevision.txt");

    static void CmdBuild()
    {
        var args = System.Environment.GetCommandLineArgs();
        var idx = System.Array.IndexOf(args, ARG_NAME);
        if (idx > 0 && idx + 1 < args.Length)
        {
            Dictionary<OptName, string> optArgs = new Dictionary<OptName, string>();

            string optStr = args[idx + 1];
            var optList = optStr.Split(OPT_SEP);
            foreach (var opt in optList)
            {
                if (opt != null && opt.Length > 1)
                {
                    var kv = opt.Split(OPT_KV_SEP);
                    if (System.Enum.IsDefined(typeof(OptName), kv[0]))
                    {
                        var k = (OptName)System.Enum.Parse(typeof(OptName), kv[0], true);
                        var v = kv[1];
                        optArgs.Add(k, v);
                    }
                }
            }
            Build(optArgs);
        }
    }

    public static void BuildForTarget(BuildTarget target)
    {
        List<string> levels = new List<string>();
        foreach (var s in EditorBuildSettings.scenes)
        {
            if (s.enabled)
                levels.Add(s.path);
        }
        if (levels.Count > 0)
        {
            var outPath = EditorUtility.SaveFilePanel("Build Player", Path.GetDirectoryName(Application.dataPath), string.Empty, string.Empty);
            if (string.IsNullOrEmpty(outPath)) { return; }

            switch (target)
            {
                case BuildTarget.Android:
                    outPath = Path.ChangeExtension(outPath, "apk");
                    break;
                case BuildTarget.iPhone:
                    outPath = Path.ChangeExtension(outPath, null);
                    break;
                case BuildTarget.StandaloneOSXIntel:
                case BuildTarget.StandaloneOSXIntel64:
                case BuildTarget.StandaloneOSXUniversal:
                    outPath = Path.ChangeExtension(outPath, "app");
                    break;
                case BuildTarget.StandaloneWindows:
                case BuildTarget.StandaloneWindows64:
                    outPath = Path.Combine(Path.ChangeExtension(outPath, null), "bin.exe");
                    break;
                default:
                    Debug.LogError("only support platforms: android/ios/win/osx");
                    break;
            }

            if (target != EditorUserBuildSettings.activeBuildTarget)
            {
                EditorUserBuildSettings.SwitchActiveBuildTarget(target);
            }

            //EditorMenuTools.SvnInfo(Path.GetDirectoryName(Application.dataPath), "Revision: ", BuildRevFilePath);
            var error = BuildPipeline.BuildPlayer(levels.ToArray(), outPath, target, BuildOptions.None);
            if (!string.IsNullOrEmpty(error))
            {
                Debug.LogError(error);
            }

            if (File.Exists(BuildRevFilePath))
            {
                File.Delete(BuildRevFilePath);
                File.Delete(BuildRevFilePath + ".meta");
            }
        }
        else
        {
            Debug.LogError("No enabled scene found in build setting");
        }
    }

    static void Build(Dictionary<OptName, string> optArgs)
    {
        BuildTarget bt = EditorUserBuildSettings.activeBuildTarget;
        if (optArgs.ContainsKey(OptName.BuildTarget))
        {
            switch (optArgs[OptName.BuildTarget])
            {
                case "ios":
                    bt = BuildTarget.iPhone;
                    break;
                case "android":
                    bt = BuildTarget.Android;
                    break;
                case "win":
                    bt = BuildTarget.StandaloneWindows;
                    break;
                case "osx":
                    bt = BuildTarget.StandaloneOSXIntel;
                    break;
            }
            EditorUserBuildSettings.SwitchActiveBuildTarget(bt);
        }


        string outPath = Application.dataPath;
        foreach (var kv in optArgs)
        {
            switch (kv.Key)
            {
                case OptName.Identifier:
                    PlayerSettings.bundleIdentifier = kv.Value;
                    break;
                case OptName.VerCode:
                    PlayerSettings.Android.bundleVersionCode = int.Parse(kv.Value);
                    break;
                case OptName.VerName:
                    PlayerSettings.bundleVersion = kv.Value;
                    break;
                case OptName.DevBuild:
                    EditorUserBuildSettings.development = bool.Parse(kv.Value);
                    break;
                case OptName.OutPath:
                    outPath = kv.Value;
                    switch (bt)
                    {
                        case BuildTarget.iPhone:
                            if (Path.HasExtension(outPath))
                                outPath = Path.ChangeExtension(outPath, null);
                            break;
                        case BuildTarget.Android:
                            if (!Path.HasExtension(outPath))
                                outPath += ".apk";
                            break;
                        case BuildTarget.StandaloneWindows:
                            if (!Path.HasExtension(outPath))
                                outPath += "/game.exe";
                            break;
                        case BuildTarget.StandaloneOSXIntel:
                            if (!Path.HasExtension(outPath))
                                outPath += ".app";
                            break;
                    }
                    var dirName = Path.HasExtension(outPath) ? Path.GetDirectoryName(outPath) : outPath;
                    if (!Directory.Exists(dirName))
                    {
                        Directory.CreateDirectory(dirName);
                    }
                    break;
                case OptName.ScriptSymbols:
                    switch (bt)
                    {
                        case BuildTarget.Android:
                            PlayerSettings.SetScriptingDefineSymbolsForGroup(BuildTargetGroup.Android, kv.Value);
                            break;
                        case BuildTarget.StandaloneGLESEmu:
                        case BuildTarget.StandaloneLinux:
                        case BuildTarget.StandaloneLinux64:
                        case BuildTarget.StandaloneLinuxUniversal:
                        case BuildTarget.StandaloneOSXIntel:
                        case BuildTarget.StandaloneOSXIntel64:
                        case BuildTarget.StandaloneOSXUniversal:
                        case BuildTarget.StandaloneWindows:
                        case BuildTarget.StandaloneWindows64:
                            PlayerSettings.SetScriptingDefineSymbolsForGroup(BuildTargetGroup.Standalone, kv.Value);
                            break;
                        case BuildTarget.iPhone:
                            PlayerSettings.SetScriptingDefineSymbolsForGroup(BuildTargetGroup.iPhone, kv.Value);
                            break;
                    }
                    break;
                case OptName.BuildTarget:
                    break;
            }
        }

        if (optArgs.ContainsKey(OptName.OutPath))
        {
            List<string> levels = new List<string>();
            foreach (var s in EditorBuildSettings.scenes)
            {
                if (s.enabled)
                    levels.Add(s.path);
            }
            if (levels.Count > 0)
            {
                if (BuildPreprocess != null)
                {
                    BuildPreprocess();
                }

                //EditorMenuTools.SvnInfo(Path.GetDirectoryName(Application.dataPath), "Revision: ", BuildRevFilePath);
                var ret = BuildPipeline.BuildPlayer(levels.ToArray(), outPath, bt,
                    EditorUserBuildSettings.development ? BuildOptions.Development : BuildOptions.None);
                if (!string.IsNullOrEmpty(ret))
                {
                    Debug.LogError(ret);
                }

                if (BuildPostprocess != null)
                {
                    if (File.Exists(BuildRevFilePath))
                    {
                        File.Delete(BuildRevFilePath);
                        File.Delete(BuildRevFilePath + ".meta");
                    }
                    BuildPostprocess();
                }
            }
            else
            {
                EditorApplication.Exit(-1);
            }
        }
    }
}