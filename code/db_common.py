#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json

def fj_function(url_content,beg_str,end_str):
    '''输入文本内容、起始文本、结束文本，截取中间文本，不包含起始和结束文本。
    隐含bug：编码
    :param url_content:
    :param beg_str:
    :param end_str:
    :return:
    '''
    if not url_content: return '',''
    str_len=len(beg_str)
    start=url_content.find(beg_str,0)
    obj=''
    if start>=0:
        content=url_content[start+str_len:]
        if end_str<>'':
            end=content.find(end_str)
            obj=content[0:end]
            content=content[end:]
    else:
        content=url_content
    return content,obj


def GetJsonValue(jsonStr,*args):
    try:
        if len(args)<=0:
            return None
        if type(jsonStr) != dict:
            jsonDict = json.loads(jsonStr)
        else:
            jsonDict = jsonStr
        return GetJsonValueByKeys(jsonDict,args)
    except:
        return None


def GetJsonValueByKeys(jsonDict,keys):
    import types
    if (type(keys) is not types.ListType and  type(keys) is not types.TupleType
        or type(jsonDict) is not types.DictType):
        return None
    jsonDictTemp=jsonDict
    try:
        count = 0
        for key in keys:
            if type(jsonDictTemp) is types.DictType:
                jsonDictTemp= GetJsonValueByKey(jsonDictTemp,key)
            elif type(jsonDictTemp) is types.ListType:
                valueObj=None
                for l in jsonDictTemp:
                    valueObj = GetJsonValueByKey(l,key)
                    if valueObj <> None:
                        break
                if valueObj<>None:
                    jsonDictTemp=valueObj
                else:
                    jsonDictTemp=None
            if(count==len(keys)-1):
                return jsonDictTemp
            if jsonDictTemp==None:
                return None
            count = count+1
    except:
        return None


def GetJsonValueByKey(jsonDict,key):
    import types
    try:
        if type(jsonDict) is types.DictType :
            if jsonDict.has_key(key):
                return jsonDict[key]
            else:
                valueObj = None
                for k in jsonDict.keys():
                    if  type(jsonDict[k]) is types.DictType:
                        valueObj = GetJsonValueByKey(jsonDict[k],key)
                    elif type(jsonDict[k]) is types.ListType:
                        for l in jsonDict[k]:
                            valueObj = GetJsonValueByKey(l,key)
                    if valueObj <> None:
                            return valueObj
        else:
            return None
    except:
        return None