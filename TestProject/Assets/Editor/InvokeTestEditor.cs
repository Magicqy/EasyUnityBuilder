using UnityEngine;
using UnityEditor;

#if TEST_EXAMPLES
static class Examples
{
    [MenuItem("Invoker/Test Examples")]
    static void TestExamples()
    {
        TestInvoke("Normal.Test_Void");

        TestInvoke("Normal.Test_Int 123");
        TestInvoke("Normal.Test_Int -321");
        //TestInvoke("Normal.Test_Int 3.3");//will failed
        //TestInvoke("Normal.Test_Int abc");//will failed

        TestInvoke("Normal.Test_String abc");
        TestInvoke("Normal.Test_String 123");

        TestInvoke("Normal.Test_Enum 0");
        TestInvoke("Normal.Test_Enum Type1");
        //TestInvoke("Normal.Test_Enum foo");//will failed

        TestInvoke("Normal.Test_Optional 0.2");
        TestInvoke("Normal.Test_Optional 3.6 20");

        TestInvoke("Normal.Test_Array [1,2,3]");

        TestInvoke("Normal.Test_ReturnValue 10", -10);

        //TestInvoke("Normal.Test_Exception");//will failed

        TestInvoke("Normal.Test_Property", "Test_Property");
        TestInvoke("Normal.Test_Property set_property_value");

        TestInvoke("Normal.Test_Overload");
        TestInvoke("Normal.Test_Overload 30");
        TestInvoke("Normal.Test_Overload true");
        //TestInvoke("Normal.Test_Overload 5.5");//will failed

        TestInvoke("Outer+Nest.Test_Nest 100", 100);

        TestInvoke("TopNS.SubNS.Outter+Nest.Test_NameSpace 200", 200);

        TestInvoke("InvokeTest.Test_Runtime");
        TestInvoke("InvokeTestEditor.Test_RuntimeEditor");
        TestInvoke("InvokeTestPlugins.Test_Plugins");
        TestInvoke("InvokeTestPluginsEditor.Test_PluginsEditor");

        TestInvoke("UnityEngine.Application.dataPath", Application.dataPath);
        //TestInvoke("Camera.allCamerasCount");//will failed

        TestInvoke("UnityEditor.EditorUserBuildSettings.activeBuildTarget", EditorUserBuildSettings.activeBuildTarget);
        TestInvoke("UnityEditor:UnityEditor.EditorUtility.FormatBytes 1024", EditorUtility.FormatBytes(1024));

        TestInvoke("mscorlib:System.Environment.CurrentDirectory", System.Environment.CurrentDirectory);
    }

    static void TestInvoke(string invokeStr, object expectedRet = null)
    {
        try
        {
            var args = invokeStr.Split(' ');
            var invokeRet = Invoker.InvokeExplict(args);
            Debug.Assert(expectedRet != null ? expectedRet.Equals(invokeRet) : expectedRet == invokeRet,
                string.Format("Assertion failed for:{0}, return value is:{1}, expected:{2}", invokeStr, invokeRet, expectedRet));
        }
        catch (System.Exception e)
        {
            Debug.LogException(e);
        }
    }
}
#endif

class InvokeTestEditor
{
    static void Test_RuntimeEditor()
    {
        Debug.Log("[InvokeExamples] InvokeTestEditor.Test_RuntimeEditor(void) is called");
    }
}