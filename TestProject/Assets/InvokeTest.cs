using UnityEngine;

class Normal
{
    static void Test_Void()
    {
        Debug.Log("[InvokeExamples] Normal.Test_Void");
    }

    static void Test_Int(int val)
    {
        Debug.LogFormat("[InvokeExamples] Normal.Test_Int(int val) val = {0}", val);
    }

    static void Test_String(string val)
    {
        Debug.LogFormat("[InvokeExamples] Normal.Test_String(string val) val = {0}", val);
    }

    public enum CustomEnumType
    {
        Type0 = 0,
        Type1 = 1,
    }

    static void Test_Enum(CustomEnumType val)
    {
        Debug.LogFormat("[InvokeExamples] Normal.Test_Enum(CustomEnumType val) val = {0}", val);
    }

    static void Test_Optional(float val, int opt = 100)
    {
        Debug.LogFormat("[InvokeExamples] Normal.Test_Optional(int val, int opt = 100) val = {0}, opt = {1}", val, opt);
    }

    static void Test_Array(int[] val)
    {
        var sb = new System.Text.StringBuilder("[");
        for (int i = 0; i < val.Length; i++)
        {
            sb.Append(val[i]);
            if (i + 1 < val.Length)
            {
                sb.Append(',');
            }
        }
        sb.Append(']');
        Debug.LogFormat("[InvokeExamples] Normal.Test_Array(int[] val) val = {0}", sb.ToString());
    }

    static int Test_ReturnValue(int val)
    {
        var ret = -val;
        Debug.LogFormat("[InvokeExamples] Normal.Test_ReturnValue(int val) val = {0}, return value is: {1}", val, ret);
        return ret;
    }

    static void Test_Exception()
    {
        Debug.LogFormat("[InvokeExamples] Normal.Test_Exception");
        throw new System.Exception("test exception intentionally made in method Normal.Test_Exception");
    }

    static string Test_Property
    {
        get
        {
            Debug.LogFormat("[InvokeExamples] Normal.Test_Property get property method");
            return "Test_Property";
        }
        set
        {
            Debug.LogFormat("[InvokeExamples] Normal.Test_Property set property method value = {0}", value);
        }
    }

    static void Test_Overload()
    {
        Debug.Log("[InvokeExamples] Normal.Test_Overload(void)");
    }

    static void Test_Overload(bool val)
    {
        Debug.LogFormat("[InvokeExamples] Normal.Test_Overload(bool val), val = {0}", val);
    }

    static void Test_Overload(int val)
    {
        Debug.LogFormat("[InvokeExamples] Normal.Test_Overload(int val), val = {0}", val);
    }

    static void Test_Overload(string val)
    {
        Debug.LogFormat("[InvokeExamples] Normal.Test_Overload(string val), val = {0}", val);
    }
}

class Outer
{
    class Nest
    {
        static int Test_Nest(int val)
        {
            Debug.LogFormat("[InvokeExamples] Outer.Nest.Test_Nest(int val) val = {0}", val);
            return val;
        }
    }
}

namespace TopNS
{
    namespace SubNS
    {
        class Outter
        {
            class Nest
            {
                static int Test_NameSpace(int val)
                {
                    Debug.LogFormat("[InvokeExamples] TopNS.SubNS.Outter+Nest.Test_NameSpace(int val) val = {0}", val);
                    return val;
                }
            }
        }
    }
}

class InvokeTest
{
    static void Test_Runtime()
    {
        Debug.LogFormat("[InvokeExamples] InvokeTest.Test_Runtime(void) is called");
    }
}