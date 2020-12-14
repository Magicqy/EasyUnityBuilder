using UnityEditor;
#if UNITY_IOS
using UnityEditor.iOS.Xcode;
#endif
using System.Collections.Generic;

//try avoid type name conflict with prefix
public static class _BuildUtility
{
    public static void AppendSymbolsForGroup(BuildTargetGroup group, string symbols)
    {
        var lastSymbols = PlayerSettings.GetScriptingDefineSymbolsForGroup(group);
        var newSymbols = string.IsNullOrEmpty(symbols) ? new List<string>() : new List<string>(symbols.Split(';'));
        newSymbols.RemoveAll(item => lastSymbols.Contains(item));
        newSymbols.Insert(0, lastSymbols);
        PlayerSettings.SetScriptingDefineSymbolsForGroup(group, string.Join(";", newSymbols.ToArray()));
    }

    public static void DeleteSymbolsForGroup(BuildTargetGroup group, string symbols)
    {
        var lastSymbols = PlayerSettings.GetScriptingDefineSymbolsForGroup(group);
        var newSymbols = string.IsNullOrEmpty(lastSymbols) ? new List<string>() : new List<string>(lastSymbols.Split(';'));
        var deleteSymbols = string.IsNullOrEmpty(symbols) ? new List<string>() : new List<string>(symbols.Split(';'));
        newSymbols.RemoveAll(item => deleteSymbols.Contains(item));
        PlayerSettings.SetScriptingDefineSymbolsForGroup(group, string.Join(";", newSymbols.ToArray()));
    }

    public static void BuildPlayer(string outPath, BuildTarget target, BuildOptions opt)
    {
        if (target != EditorUserBuildSettings.activeBuildTarget)
        {
            throw new System.Exception(string.Format("activeBuildTarget is not {0}", target));
        }

        List<string> levels = new List<string>();
        foreach (var s in EditorBuildSettings.scenes)
        {
            if (s.enabled)
                levels.Add(s.path);
        }

        if (levels.Count > 0)
        {
            var result = BuildPipeline.BuildPlayer(levels.ToArray(), outPath, target, opt);
#if UNITY_2017_1_OR_NEWER
            if (result.summary.result != UnityEditor.Build.Reporting.BuildResult.Succeeded)
            {
                throw new System.Exception(string.Format("BuildResult {0}, {1} erorrs, {2} warnings",
                    result.summary.result, result.summary.totalErrors, result.summary.totalWarnings));
            }
#else
            if (!string.IsNullOrEmpty(result))
            {
                throw new System.Exception(result);
            }
#endif
        }
        else
        {
            throw new System.Exception("There is no enabled scene found in build settings");
        }
    }

    //setting path for android external tools, fix path missing when run from jenkins
    public static void SetAndroidSdkPath(string androdiSdkPath, string javaPath, string androidNdkPath)
    {
        EditorPrefs.SetString("AndroidSdkRoot", androdiSdkPath);
        EditorPrefs.SetString("JdkPath", javaPath);
        EditorPrefs.SetString("AndroidNdkRoot", androidNdkPath);
    }

#if UNITY_IOS
    public static void EnableXCodeProjectBitCode(BuildTarget buildTarget, string xprojPath)
    {
        if (buildTarget == BuildTarget.iOS)
        {
            string projFilePath = Path.Combine(xprojPath, "Unity-iPhone.xcodeproj/project.pbxproj");

            if (File.Exists(projFilePath))
            {
                PBXProject pbxProject = new PBXProject();
                pbxProject.ReadFromFile(projFilePath);

                string target = pbxProject.TargetGuidByName("Unity-iPhone");
                pbxProject.SetBuildProperty(target, "ENABLE_BITCODE", "NO");

                pbxProject.WriteToFile(projFilePath);
            }
        }
    }
#endif
}