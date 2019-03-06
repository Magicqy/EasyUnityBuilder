/**
 *  Invoke static method from command-line
 * 
 *  Usage:
 *      $UNITY_HOME/Unity.exe -projectPath $PROJECT_PATH -batchmode -quit [-invokeLog $LOG_PATH] \
 *          -executeMethod Invoker.InvokeCommandLine $METHOD $PARAMETERS [-next $METHOD $PARAMETERS]
 *      Use '-next' to chain the invoke.
 *      
 *      METHOD:
 *          [Assembly:(Optional)]Namespace.SubNamespace.Class+NestedClass.Method
 *          Check Type.AssemblyQualifiedName property for more information
 *          Type name startwith UnityEngine. or UnityEditor. will search in UnityEngine.dll and UnityEditor.dll.
 *          Other type names will searched in all CSharp scripts in 'Assets' folder.
 *          Provide type name with assembly name together can search in custom dlls.
 *      
 *      PARAMETERS: 
 *          Support types: primitive value types(int, float, bool, etc.) / enum / string / array
 *          Array parameter are identitfied by tag [$ARRAY_ITEMS], items are sperated by comma(,), eg: invoke method foo(int[] arr) with [4,6,8].
 *      
 *  Note:
 *      Exit Unity Editor application like call EditorApplication.Exit(1) in your invoke method will lost Invoker's log on MacOS,
 *      because finally block does not work when exception occurs, it's a bug of Mono on MacOS. (Tested in in Unity5.x)
 * 
 *  Examples Calls:
 *      See InvokerTestEditor.cs
 *      
 *  Author:     Qu Yong
 *  Version:    1.0.0
 *  Date:       2015-08-05
 *  Email:      work.qu@outlook.com
 */
using UnityEngine;
using UnityEditor;
using System;
using System.IO;
using System.Collections.Generic;
using System.Reflection;

public static class Invoker
{
    const string INVOKER_METHOD_NAME = "Invoker.InvokeCommandLine";
    const string TAG_NEXT_INVOKE = "-next";
    const string TAG_INVOKE_LOG = "-invokeLog";
    const string ASM_NAME_CSHARP = "Assembly-CSharp";
    const string ASM_NAME_CSHARP_EDITOR = "Assembly-CSharp-Editor";
    const string ASM_NAME_CSHARP_EDITOR_FP = "Assembly-CSharp-Editor-firstpass";
    const string ASM_NAME_CSHARP_FP = "Assembly-CSharp-firstpass";
    const string PATTERN_ENGINE_TYPES = "UnityEngine.";
    const string NAMESPACE_ENGINE = "UnityEngine";
    const string PATTERN_EDITOR_TYPES = "UnityEditor.";
    const string NAMESPACE_EDITOR = "UnityEditor";
    const char TAG_ARG_SEP = '|';
    const char TAG_ARRAY_BEG = '[';
    const char TAG_ARRAY_END = ']';
    const char TAG_ARRAY_SEP = ',';


    /// <summary>
    /// 通过命令行调用方法入口
    /// </summary>
    static void InvokeCommandLine()
    {
        int exitCode = 0;
        try
        {
            var cmdArgs = Environment.GetCommandLineArgs();

            var index = Array.IndexOf(cmdArgs, TAG_INVOKE_LOG);
            string logFilePath = null;
            if (index > 0 && index + 1 < cmdArgs.Length)
            {
                logFilePath = cmdArgs[index + 1];
            }

            index = Array.IndexOf(cmdArgs, INVOKER_METHOD_NAME);
            if (index > 0 && index + 1 < cmdArgs.Length)
            {
                var invokeArgs = new List<string>();
                while (index < cmdArgs.Length)
                {
                    invokeArgs.Clear();
                    for (int i = index + 1; i < cmdArgs.Length; index = ++i)
                    {
                        var argStr = cmdArgs[i];
                        if (argStr == TAG_NEXT_INVOKE)
                        {
                            //break for next invoke
                            break;
                        }
                        invokeArgs.Add(argStr);
                    }
                    InvokeExplict(invokeArgs.ToArray(), logFilePath);
                }
            }
            else
            {
                ThrowInvokerExcpetion("Invalid command line arguments");
            }
        }
        catch
        {
            exitCode = 1;
        }
        finally
        {
            if (exitCode != 0)
            {
                //Mono on mac does not fully support try-catch-finally, finally block will not be called when application exit from catch block.
                EditorApplication.Exit(exitCode);
            }
        }
    }

    /// <summary>
    /// 使用显示参数列表调用方法
    /// </summary>
    public static object InvokeExplict(string[] args, string logFilePath = null)
    {
        try
        {
            Logger.Open(logFilePath);
            Logger.WriteLine("---------Invoke Begin---------");
            return InvokeInternal(args);
        }
        catch (Exception e)
        {
            Logger.WriteLine("---------Exception Occured---------");
            Logger.WriteLine(e);
            throw e;
        }
        finally
        {
            Logger.WriteLine("---------Invoke End---------");
            Logger.Flush();
        }
    }

    static object InvokeInternal(string[] invokeArgs)
    {
        if (invokeArgs == null || invokeArgs.Length == 0)
        {
            ThrowInvokerExcpetion("Insufficient invoke arguments");
        }

        var invokeStr = invokeArgs[0];
        //try get assembly name
        string assemblyName = null;
        var indexOf = invokeStr.IndexOf(':');
        if (indexOf > 0)
        {
            assemblyName = invokeStr.Substring(0, indexOf);
            invokeStr = invokeStr.Substring(indexOf + 1);
        }

        //get method name
        indexOf = invokeStr.LastIndexOf('.');
        if (indexOf <= 0)
        {
            ThrowInvokerExcpetion("Method name not found in invoke arguments:" + invokeStr);
        }

        var typeName = invokeStr.Substring(0, indexOf);
        var methodName = invokeStr.Substring(indexOf + 1);
        var paramStrings = new List<string>();
        for (int i = 1; i < invokeArgs.Length; i++)
        {
            paramStrings.Add(invokeArgs[i]);
        }
        return InvokeStatic(assemblyName, typeName, methodName, paramStrings);
    }

    /// <summary>
    /// 调用一个类中的静态方法
    /// </summary>
    static object InvokeStatic(string assemblyName, string typeName, string methodName, List<string> paramStrings)
    {
        Logger.WriteLine("AssemblyName:     {0}", assemblyName);
        Logger.WriteLine("TypeName:         {0}", typeName);
        Logger.WriteLine("MethodName:       {0}", methodName);
        Logger.WriteLine("ParameterCount:  {0}", paramStrings.Count);
        for (int i = 0; i < paramStrings.Count; i++)
        {
            Logger.WriteLine("[{0}]  =>  {1}", i + 1, paramStrings[i]);
        }

        Logger.WriteLine("---------Match Method---------");
        var typeInfo = MatchType(typeName, assemblyName);
        if (typeInfo == null)
        {
            ThrowInvokerExcpetion("Type match failed:" + typeName);
        }

        //TODO 调用方法时如何匹配参数？
        //使用Type.GetMethod在方法有重载的时候无法很完备的进行匹配，当参数数量相同但类型不同则无法优先匹配最合适的方法
        //另一种方式是使用Type.InvokeMember来调用方法，但问题出在于无法预知方法的参数列表类型来将参数字符串转换成方法声明中的参数类型
        //或许可以参考System.Reflection.Binder来实现自定义参数匹配策略
        //type.InvokeMember(methodName,
        //    BindingFlags.Static | BindingFlags.InvokeMethod |
        //    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.FlattenHierarchy,
        //    Type.DefaultBinder, null, ???);

        List<object> parsedParamValues;
        var methodInfo = MatchMethod(typeInfo, methodName,
            BindingFlags.Static | BindingFlags.InvokeMethod |
            BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.FlattenHierarchy,
            paramStrings, out parsedParamValues);
        if (methodInfo == null)
        {
            ThrowInvokerExcpetion("Method match failed:" + methodName);
        }

        Logger.WriteLine("Method Matched:  {0}", methodInfo.Name);
        Logger.WriteLine("---------Invoke Result---------");
        var result = methodInfo.Invoke(null, parsedParamValues.ToArray());
        Logger.WriteLine(result != null ? result.ToString() : "null");
        return result;
    }

    /// <summary>
    /// 显示指定AssemblyName或者使用尝试在默认的几个Assembly中查找
    /// Ref:    Unity Manual - Scripting - Scripting Overview - Special Folders and Script Compilation Order
    /// </summary>
    static Type MatchType(string typeName, string assemblyName)
    {
        if (string.IsNullOrEmpty(assemblyName))
        {
            //尝试在Unity引擎程序集提供的类型中查找
            if (typeName.StartsWith(PATTERN_ENGINE_TYPES))
            {
                return GetTypeOfUnity(typeName, NAMESPACE_ENGINE);
            }
            else if (typeName.StartsWith(PATTERN_EDITOR_TYPES))
            {
                return GetTypeOfUnity(typeName, NAMESPACE_EDITOR);
            }
            else
            {
                //尝试在Plugins之外的Editor目录中查找
                var type = GetTypeByName(typeName, Assembly.Load(ASM_NAME_CSHARP_EDITOR));
                if (type != null)
                {
                    return type;
                }

                //尝试在Plugins中的Editor目录中查找
                type = GetTypeByName(typeName, Assembly.Load(ASM_NAME_CSHARP_EDITOR_FP));
                if (type != null)
                {
                    return type;
                }

                //尝试在Plugins之外的非Editor目录中查找
                type = GetTypeByName(typeName, Assembly.Load(ASM_NAME_CSHARP));
                if (type != null)
                {
                    return type;
                }

                //尝试在Plugins中的非Editor目录查找
                type = GetTypeByName(typeName, Assembly.Load(ASM_NAME_CSHARP_FP));
                if (type != null)
                {
                    return type;
                }
            }
            return null;
        }
        else
        {
            //直接匹配给定的类型全名
            return GetTypeByName(typeName, Assembly.Load(assemblyName));
        }
    }

    static Type GetTypeByName(string typeName, Assembly asm)
    {
        var type = asm.GetType(typeName, false, true);
        var found = type != null;
        Logger.WriteLine("Type {0}: {1}, {2}", found ? "found" : "not found", typeName, asm.GetName().Name);
        return type;
    }

    static Type GetTypeOfUnity(string typeName, string moduleName)
    {
        Type type = null;
        foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
        {
            var asmName = asm.GetName().Name;
            if (asmName.StartsWith(moduleName))
            {
                type = asm.GetType(typeName, false, true);
                if (type != null)
                {
                    break;
                }
            }
        }
        var found = type != null;
        Logger.WriteLine("Type {0}: {1}, {2}", found ? "found" : "not found", typeName, moduleName);
        return type;
    }

    /// <summary>
    /// 匹配一个类型中的特定名称的方法
    /// </summary>
    static MethodInfo MatchMethod(Type type, string methodName,
        BindingFlags bindingAttr, List<string> paramStrings, out List<object> parsedParamValues)
    {
        parsedParamValues = null;
        try
        {
            var methodInfo = type.GetMethod(methodName, bindingAttr);
            if (methodInfo == null)
            {
                //match method as property getter and setter
                if (paramStrings.Count == 0 || paramStrings.Count == 1)
                {
                    Logger.WriteLine("No method found in type: {0}, try match as property name: {0}", type.Name, methodName);
                    var prop = type.GetProperty(methodName, bindingAttr);
                    if (prop != null)
                    {
                        methodInfo = paramStrings.Count == 0 ? prop.GetGetMethod(true) : prop.GetSetMethod(true);
                    }
                }
            }
            if (methodInfo != null)
            {
                return MatchParameters(methodInfo, paramStrings, out parsedParamValues) ? methodInfo : null;
            }
        }
        catch (AmbiguousMatchException)
        {
            Logger.WriteLine("AmbiguousMatchException occured, match by method name failed, try match by parameters");
        }

        var methods = type.GetMethods(bindingAttr);
        foreach (var item in methods)
        {
            var paramInfoList = item.GetParameters();
            var paramInfoCount = paramInfoList.Length;
            if (item.Name == methodName)
            {
                if (paramInfoCount == paramStrings.Count)
                {
                    //尝试匹配参数数目相同的方法
                    if (MatchParameters(item, paramStrings, out parsedParamValues))
                    {
                        return item;
                    }
                }
                else if (paramInfoCount > paramStrings.Count && paramInfoList[paramStrings.Count].IsOptional)
                {
                    //尝试匹配有可选参数的情况
                    if (MatchParameters(item, paramStrings, out parsedParamValues))
                    {
                        return item;
                    }
                }
            }
        }
        return null;
    }

    /// <summary>
    /// 根据输入的参数列表判断一个方法是否适合调用，并尝试将输入参数转化为对应的类型
    /// </summary>
    static bool MatchParameters(MethodInfo candidate, List<string> paramStrings, out List<object> parsedParamValues)
    {
        parsedParamValues = new List<object>();
        var allMatched = true;
        var parameters = candidate.GetParameters();
        for (int i = 0; i < parameters.Length; i++)
        {
            var param = parameters[i];
            if (i < paramStrings.Count)
            {
                var paramStr = paramStrings[i];
                object paramVal;
                var matched = TryConvertParamValue(paramStr, param.ParameterType, out paramVal);
                Logger.WriteLine("Positional Parameter: {0} => {1} {2} = {3},   matched:{4}", paramStr, param.ParameterType.Name, param.Name, paramVal, matched);
                if (matched)
                {
                    parsedParamValues.Add(paramVal);
                }
                else
                {
                    allMatched = false;
                    break;
                }
            }
            else if (param.IsOptional)
            {
                var paramVal = param.DefaultValue;
                var matched = true;
                Logger.WriteLine("Optional Parameter:   {0} {1} = {2},   matched:{3}", param.ParameterType.Name, param.Name, paramVal, matched);
                if (matched)
                {
                    parsedParamValues.Add(paramVal);
                }
            }
            else
            {
                Logger.WriteLine("Paramter not enough");
                allMatched = false;
                break;
            }
        }
        return allMatched;
    }

    /// <summary>
    /// 尝试转换参数的类型
    /// </summary>
    static bool TryConvertParamValue(string paramStr, Type targetType, out object paramVal)
    {
        paramVal = null;
        try
        {
            if (targetType.IsEnum)
            {
                if (paramStr.IndexOf(TAG_ARG_SEP) > 0)
                {
                    int resVal = 0;
                    bool nothingParsed = true;
                    foreach (var eStr in paramStr.Split(TAG_ARG_SEP))
                    {
                        if (Enum.IsDefined(targetType, eStr))
                        {
                            resVal |= Convert.ToInt32(Enum.Parse(targetType, eStr));
                            nothingParsed = false;
                        }
                        else
                        {
                            int eVal;
                            if (int.TryParse(eStr, out eVal) && Enum.IsDefined(targetType, eVal))
                            {
                                resVal |= eVal;
                                nothingParsed = false;
                            }
                        }
                    }
                    paramVal = nothingParsed ? null : Enum.ToObject(targetType, resVal);
                }
                else
                {
                    if (Enum.IsDefined(targetType, paramStr))
                    {
                        paramVal = Enum.Parse(targetType, paramStr);
                    }
                    else
                    {
                        int val;
                        if (int.TryParse(paramStr, out val) && Enum.IsDefined(targetType, val))
                        {
                            paramVal = Enum.ToObject(targetType, val);
                        }
                    }
                }
            }
            else if (targetType.IsArray)
            {
                if (paramStr.Length > 2 && paramStr[0] == TAG_ARRAY_BEG && paramStr[paramStr.Length - 1] == TAG_ARRAY_END)
                {
                    var eleStrs = paramStr.Substring(1, paramStr.Length - 2).Split(TAG_ARRAY_SEP);
                    var eleType = targetType.GetElementType();
                    if (eleType.IsPrimitive || eleType.IsEnum || eleType == typeof(string))
                    {
                        var suc = true;
                        var arr = Array.CreateInstance(eleType, eleStrs.Length);
                        for (int i = 0; i < eleStrs.Length && suc; i++)
                        {
                            object eleVal;
                            suc &= TryConvertParamValue(eleStrs[i], eleType, out eleVal);
                            arr.SetValue(eleVal, i);
                        }
                        if (suc)
                        {
                            paramVal = arr;
                        }
                    }
                }
            }
            else
            {
                paramVal = Convert.ChangeType(paramStr, targetType);
            }
        }
        catch
        {
            return false;
        }
        return paramVal != null;
    }

    static void ThrowInvokerExcpetion(string msg)
    {
        throw new Exception(string.Format("[InvokerExcpetion]   {0}", msg));
    }

    private static class Logger
    {
        static TextWriter logWriter = TextWriter.Null;

        public static void Open(string logFilePath = null)
        {
            if (string.IsNullOrEmpty(logFilePath))
            {
                logWriter = new StringWriter();
            }
            else
            {
                var sw = new StreamWriter(logFilePath, true);
                sw.AutoFlush = true;
                logWriter = sw;
            }
        }

        public static void Flush()
        {
            if (logWriter != TextWriter.Null)
            {
                if (logWriter is StringWriter)
                {
                    Debug.Log((logWriter as StringWriter).ToString());
                }
                logWriter.Dispose();
                logWriter = null;
            }
        }

        public static void WriteLine(string arg)
        {
            logWriter.WriteLine(arg);
        }

        public static void WriteLine(object arg)
        {
            logWriter.WriteLine(arg);
        }

        public static void WriteLine(string fmt, object arg0)
        {
            logWriter.WriteLine(fmt, arg0);
        }

        public static void WriteLine(string fmt, object arg0, object arg1)
        {
            logWriter.WriteLine(fmt, arg0, arg1);
        }

        public static void WriteLine(string fmt, object arg0, object arg1, object arg2)
        {
            logWriter.WriteLine(fmt, arg0, arg1, arg2);
        }

        public static void WriteLine(string fmt, params object[] args)
        {
            logWriter.WriteLine(fmt, args);
        }
    }
}