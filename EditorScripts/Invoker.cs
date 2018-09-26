/**
 *  Invoke static method from command-line
 * 
 *  Usage:
 *      $UNITY_HOME/Unity.exe -projectPath $PROJECT_PATH -batchmode -quit -executeMethod Invoker.Invoke $METHOD $PARAMETERS [-next METHOD PARAMETERS]
 *      Use '-next' to chain the invoke.
 *      METHOD:     [Assembly:(Optional)]Namespace.SubNamespace.Class+NestedClass.Method
 *                  Check Type.AssemblyQualifiedName property for more information
 *                  Will search in all CSharp scripts in 'Assets' folder by default.
 *      PARAMETERS: string value seperated by space, support type: primitive / enum / string.
 *      
 *  Note:
 *      Exit Unity Editor application like call EditorApplication.Exit(1) in your invoke method will lost Invoker's log on MacOS,
 *      because finally block does not work when exception occurs, it's a bug of Mono on MacOS.
 * 
 *  Examples Calls:
 *      Plugins.Hello
 *      PluginsEditor.Hello
 *      Normal.Hello
 *      Top.Sub.Class.Void
 *      Top.Sub.Class.Int32 123
 *      Top.Sub.Class.Enum iPhone
 *      Top.Sub.Class.Opt 9
 *      Top.Sub.Class.Opt 9 6
 *      Top.Sub.Class.Func 1
 *      Top.Sub.Class.Func true
 *      Top.Sub.Class.Array [1,2,3]
 *      Top.Sub.Class.IntProp 10 -next Top.Sub.Class.IntProp
 *      Top.Sub.Class+NestedClass.Hello
 *      UnityEngine:UnityEngine.Application.OpenURL www.unity3d.com
 *      UnityEditor:UnityEditor.EditorUtility.FormatBytes 1024
 *      
 *  Author:     Qu Yong
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
    const string INVOKER_METHOD_NAME = "Invoker.Invoke";
    const string TAG_NEXT_INVOKE = "-next";
    const string TAG_INVOKE_LOG = "-invokeLog";
    const string ASM_NAME_CSHARP = "Assembly-CSharp";
    const string ASM_NAME_CSHARP_EDITOR_FP = "Assembly-CSharp-Editor-firstpass";
    const string ASM_NAME_CSHARP_FP = "Assembly-CSharp-firstpass";
    const char TAG_ARG_SEP = '|';
    const char TAG_ARRAY_BEG = '[';
    const char TAG_ARRAY_END = ']';
    const char TAG_ARRAY_SEP = ',';
    

    /// <summary>
    /// 通过命令行调用方法入口
    /// </summary>
    static void Invoke()
    {
        int exitCode = 0;
        try
        {
            var cmdArgs = Environment.GetCommandLineArgs();
            var index = Array.IndexOf(cmdArgs, TAG_INVOKE_LOG);
            if (index > 0 && index + 1 < cmdArgs.Length)
            {
                Logger.Open(cmdArgs[index + 1]);
            }
            else
            {
                Logger.Open();
            }
            index = Array.IndexOf(cmdArgs, INVOKER_METHOD_NAME);
            if (index > 0 && index + 1 < cmdArgs.Length)
            {
                var argList = new List<string>();
                while (index < cmdArgs.Length)
                {
                    argList.Clear();
                    for (int i = index + 1; i < cmdArgs.Length; index = ++i)
                    {
                        var argStr = cmdArgs[i];
                        if (argStr[0] == '-')
                        {
                            if (argStr == TAG_NEXT_INVOKE)
                            {
                                //break for next invoke
                                break;
                            }
                            decimal d;
                            if (decimal.TryParse(argStr, out d) == false)
                            {
                                //unrecognized option, break all
                                index = cmdArgs.Length;
                                break;
                            }
                        }
                        argList.Add(argStr);
                    }
                    InvokeWithArgs(argList.ToArray());
                }
            }
            else
            {
                Logger.WriteLine("Nothing to invoke");
                throw new Exception("INVALID_COMMAND_LINE_ARGUMENTS");
            }
        }
        catch (Exception e)
        {
           Logger.WriteLine(e);
           exitCode = 1;
        }
        finally
        {
           Logger.Flush();
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
    public static void InvokeWithArgs(string[] args)
    {
        if (args.Length > 0)
        {
            var invokeStr = args[0];
            string assemblyName = null;
            var indexOf = invokeStr.IndexOf(':');
            if (indexOf > 0)
            {
                assemblyName = invokeStr.Substring(0, indexOf);
                invokeStr = invokeStr.Substring(indexOf + 1);
            }

            indexOf = invokeStr.LastIndexOf('.');
            if (indexOf > 0)
            {
                var typeName = invokeStr.Substring(0, indexOf);
                var methodName = invokeStr.Substring(indexOf + 1);

                var argList = new List<string>();
                for (int i = 1; i < args.Length; i++)
                {
                    var argStr = args[i];
                    if (argStr[0] == '-')
                    {
                        //数字的负号或是一个新参数开始
                        decimal val;
                        if (decimal.TryParse(argStr, out val) == false)
                            break;
                    }
                    argList.Add(args[i]);
                }
                InvokeStatic(assemblyName, typeName, methodName, argList);
            }
            else
            {
                Logger.WriteLine("Invalid arguments, method name not found.");
                throw new Exception("METHOD_NOT_FOUND");
            }
        }
        else
        {
            Logger.WriteLine("Insufficient arguments");
            throw new Exception("INVALID_INVOKE_ARGUMENTS");
        }
    }

    /// <summary>
    /// 调用一个类中的静态方法
    /// </summary>
    static void InvokeStatic(string assemblyName, string typeName, string methodName, List<string> argList)
    {
        Logger.WriteLine("---------Invoke Static---------");
        Logger.WriteLine("AssemblyName:    {0}", assemblyName);
        Logger.WriteLine("TypeName:        {0}", typeName);
        Logger.WriteLine("MethodName:      {0}", methodName);
        Logger.WriteLine("Arguments:");
        for (int i = 0; i < argList.Count; i++)
        {
            Logger.WriteLine("[{0}]  =>  {1}", i, argList[i]);
        }

        Logger.WriteLine("---------Match Method---------");
        var type = GetTypeByName(assemblyName, typeName);
        if (type != null)
        {
            ///TODO 调用方法时如何匹配参数？
            ///使用Type.InvokeMember只能接受string作为参数
            ///使用Type.GetMethod无法处理有重载方法的情况
            ///问题的关键在于无法预知方法的参数列表类型，或许可以参考System.Reflection.Binder来实现自定义参数匹配

            //type.InvokeMember(methodName,
            //    BindingFlags.Static | BindingFlags.InvokeMethod |
            //    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.FlattenHierarchy,
            //    Type.DefaultBinder, null, argList.ToArray());

            List<object> parsedArgList;
            var methodInfo = MatchMethodInfo(type, methodName,
                BindingFlags.Static | BindingFlags.InvokeMethod |
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.FlattenHierarchy,
                argList, out parsedArgList);
            if (methodInfo != null)
            {
                Logger.WriteLine("Method Matched:  {0}", methodInfo.Name);
                Logger.WriteLine("---------Invoke Result---------");
                Logger.WriteLine(methodInfo.Invoke(null, parsedArgList.ToArray()));
            }
            else
            {
                Logger.WriteLine("Method Not Found");
                throw new Exception("METHOD_NOT_FOUND");
            }
        }
        else
        {
            Logger.WriteLine("Type Not Found");
            throw new Exception("TYPE_NOT_FOUND");
        }
    }

    /// <summary>
    /// 显示指定AssemblyName或者使用尝试在默认的几个Assembly中查找
    /// Ref:    Unity Manual - Scripting - Scripting Overview - Special Folders and Script Compilation Order
    /// </summary>
    static Type GetTypeByName(string assemblyName, string typeName)
    {
        if (string.IsNullOrEmpty(assemblyName))
        {
            var type = Type.GetType(typeName, false, true);
            if (type != null) { return type; }

            //尝试在Editor和Plugins目录之外的代码中查找
            var newTypeName = string.Format("{0}, {1}", typeName, ASM_NAME_CSHARP);
            Logger.WriteLine("Retry for AssemblyQualifiedName:  {0}", newTypeName);
            type = Type.GetType(newTypeName, false, true);
            if (type != null) { return type; }

            //尝试在与顶层命名空间同名的Assembly中查找
            var index = typeName.IndexOf('.');
            if (index > 0)
            {
                newTypeName = string.Format("{0}, {1}", typeName, typeName.Substring(0, index));
                Logger.WriteLine("Retry for AssemblyQualifiedName:  {0}", newTypeName);
                type = Type.GetType(newTypeName, false, true);
                if (type != null) { return type; }
            }

            //尝试在Plugins/Editor目录的代码中查找
            newTypeName = string.Format("{0}, {1}", typeName, ASM_NAME_CSHARP_EDITOR_FP);
            Logger.WriteLine("Retry for AssemblyQualifiedName:  {0}", newTypeName);
            type = Type.GetType(newTypeName, false, true);
            if (type != null) { return type; }

            //尝试在Plugins目录中代码中查找
            newTypeName = string.Format("{0}, {1}", typeName, ASM_NAME_CSHARP_FP);
            Logger.WriteLine("Retry for AssemblyQualifiedName:  {0}", newTypeName);
            type = Type.GetType(newTypeName, false, true);
            if (type != null) { return type; }

            return null;
        }
        else
        {
            return Type.GetType(string.Format("{0}, {1}", typeName, assemblyName), false, true);
        }
    }

    /// <summary>
    /// 匹配一个类型中的特定名称的方法
    /// </summary>
    static MethodInfo MatchMethodInfo(Type type, string methodName,
        BindingFlags bindingAttr, List<string> argList, out List<object> parsedArgList)
    {
        parsedArgList = null;
        try
        {
            var methodInfo = type.GetMethod(methodName, bindingAttr);
            if (methodInfo == null)
            {
                //match method as property getter and setter
                if (argList.Count == 0 || argList.Count == 1)
                {
                    Logger.WriteLine("No method found, try match as property name");
                    var prop = type.GetProperty(methodName, bindingAttr);
                    if (prop != null)
                    {
                        methodInfo = argList.Count == 0 ? prop.GetGetMethod(true) : prop.GetSetMethod(true);
                    }
                }
            }

            return methodInfo != null && MatchMethodParameters(methodInfo, argList, out parsedArgList) ? methodInfo : null;
        }
        catch (AmbiguousMatchException) { Logger.WriteLine("AmbiguousMatchException Occured!"); }
        
        var methods = type.GetMethods(bindingAttr);
        foreach (var item in methods)
        {
            //尝试匹配参数数目相同的方法
            if (item.Name == methodName && item.GetParameters().Length == argList.Count)
            {
                if (MatchMethodParameters(item, argList, out parsedArgList))
                {
                    return item;
                }
            }
        }

        foreach (var item in methods)
        {
            //尝试匹配有可选参数的情况
            var parameters = item.GetParameters();
            if (item.Name == methodName && parameters.Length > argList.Count && parameters[argList.Count].IsOptional)
            {
                if (MatchMethodParameters(item, argList, out parsedArgList))
                {
                    return item;
                }
            }
        }

        return null;
    }

    /// <summary>
    /// 根据输入的参数列表判断一个方法是否适合调用，并尝试将输入参数转化为对应的类型
    /// </summary>
    static bool MatchMethodParameters(MethodInfo candidate, List<string> argList, out List<object> parsedArgList)
    {
        parsedArgList = new List<object>();
        var allMatched = true;
        var parameters = candidate.GetParameters();
        for (int i = 0; i < parameters.Length; i++)
        {
            var param = parameters[i];
            object result;
            if (i < argList.Count)
            {
                var argStr = argList[i];
                allMatched &= TryConvertTo(argStr, param.ParameterType, out result);
                Logger.WriteLine("Match Parameter:  {0}  =>  {1} / {2},    {3}", argStr, param.Name, param.ParameterType.Name, allMatched);
            }
            else if (param.IsOptional)
            {
                allMatched &= true;
                result = param.DefaultValue;
                Logger.WriteLine("Optional Parameter:  {0}  =>  {1} / {2},    {3}", result, param.Name, param.ParameterType.Name, allMatched);
            }
            else
            {
                allMatched &= false;
                result = null;
            }
            if (allMatched) { parsedArgList.Add(result); }
        }
        return allMatched;
    }

    /// <summary>
    /// 尝试转换参数的类型
    /// </summary>
    static bool TryConvertTo(string argStr, Type targetType, out object result)
    {
        result = null;
        try
        {
            if (targetType.IsEnum)
            {
                if (argStr.IndexOf(TAG_ARG_SEP) > 0)
                {
                    int resVal = 0;
                    bool nothingParsed = true;
                    foreach (var eStr in argStr.Split(TAG_ARG_SEP))
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
                    result = nothingParsed ? null : Enum.ToObject(targetType, resVal);
                }
                else
                {
                    if (Enum.IsDefined(targetType, argStr))
                    {
                        result = Enum.Parse(targetType, argStr);
                    }
                    else
                    {
                        int val;
                        if (int.TryParse(argStr, out val) && Enum.IsDefined(targetType, val))
                        {
                            result = Enum.ToObject(targetType, val);
                        }
                    }
                }
            }
            else if (targetType.IsArray)
            {
                if (argStr.Length > 2 && argStr[0] == TAG_ARRAY_BEG && argStr[argStr.Length - 1] == TAG_ARRAY_END)
                {
                    var eleStrs = argStr.Substring(1, argStr.Length - 2).Split(TAG_ARRAY_SEP);
                    var eleType = targetType.GetElementType();
                    if (eleType.IsPrimitive || eleType.IsEnum || eleType == typeof(string))
                    {
                        var suc = true;
                        var arr = Array.CreateInstance(eleType, eleStrs.Length);
                        for (int i = 0; i < eleStrs.Length && suc; i++)
                        {
                            object eleVal;
                            suc &= TryConvertTo(eleStrs[i], eleType, out eleVal);
                            arr.SetValue(eleVal, i);
                        }
                        if (suc) { result = arr; }
                    }
                }
            }
            else
            {
                result = Convert.ChangeType(argStr, targetType);
            }
        }
        catch { return false; }
        return result != null;
    }

    private static class Logger
    {
        static TextWriter logWriter = TextWriter.Null;

        public static void Open()
        {
            logWriter = new StringWriter();
        }

        public static void Open(string path)
        {
            var sw = new StreamWriter(path, false);
            sw.AutoFlush = true;
            logWriter = sw;
        }

        public static void Flush()
        {
            if (logWriter != TextWriter.Null)
            {
                Debug.Log(logWriter);
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

        //TextWriter defOut;
        //public Logger()
        //{
        //    defOut = Console.Out;
        //    Console.SetOut(new StreamWriter("log_invoker.txt", false));

        //    //build player for android will got Resource re-package failed error after change Console.Out to another StringWriter
        //    //Console.Out is an instance of class UnityLogWriter by default
        //    Console.SetOut(new StringWriter());
        //}

        //public static void Dispose()
        //{
        //    var sw = Console.Out;
        //    Console.SetOut(defOut);
        //    Debug.Log(sw);
        //    sw.Dispose();
        //}
    }
}
