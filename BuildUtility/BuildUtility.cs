using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEditor;
#if UNITY_IOS
using UnityEditor.iOS.Xcode;
#endif

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
        if (target != EditorUserBuildSettings.activeBuildTarget)
        {
            EditorUserBuildSettings.SwitchActiveBuildTarget(target);
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
#else
            if (!string.IsNullOrEmpty(result))
#endif
            {
                Debug.LogError(result.ToString());
                EditorApplication.Exit(1);
            }
        }
        else
        {
            Debug.LogError("There is no enabled scene found in build settings");
            EditorApplication.Exit(1);
        }
    }

#if UNITY_IOS
    public static void ModifyXCodeProject(BuildTarget buildTarget, string xprojPath)
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
