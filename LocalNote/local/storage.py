import json, os, time, sys
from markdown2 import markdown
import chardet

from evernoteapi import EvernoteController

CONFIG_DIR = 'user.cfg'

# fileDictFormat: {
# 'notebookName':[('note1', timeStamp), ..],
# }
# fileFormat: {
# 'name': "note's name",
# 'content': u''.encode('utf-8'),
# 'attachment': [('name', u''.encode),..),],
# }

class Storage(object):
    def __init__(self):
        self.token, self.isSpecialToken, self.sandbox, self.isInternational, self.expireTime, self.lastUpdate = self.__load_config()
        self.encoding = sys.stdin.encoding
    def __load_config(self):
        if not os.path.exists(CONFIG_DIR): return '', False, True, False, 0, 0
        with open(CONFIG_DIR) as f: r = json.loads(f.read())
        return r.get('token', ''), r.get('is-special-token', False), r.get('sandbox', True), r.get('is-international', False), r.get('expire-time', 0), r.get('last-update', 0)
    def __store_config(self):
        with open(CONFIG_DIR, 'w') as f:
            f.write(json.dumps({
                'token': self.token,
                'is-special-token': self.isSpecialToken,
                'sandbox': self.sandbox,
                'is-international': self.isInternational,
                'expire-time': self.expireTime,
                'last-update': self.lastUpdate, }))
    def update_config(self, token=None, isSpecialToken=None, sandbox=None, isInternational=None, expireTime=None, lastUpdate=None):
        if not token is None: self.token = token
        if not isSpecialToken is None: self.isSpecialToken = isSpecialToken
        if not sandbox is None: self.sandbox = sandbox
        if not isInternational is None: self.isInternational = isInternational
        if not expireTime is None: self.expireTime = expireTime
        if not lastUpdate is None: self.lastUpdate = lastUpdate
        self.__store_config()
    def get_config(self):
        return self.token, self.isSpecialToken, self.sandbox, self.isInternational, self.expireTime, self.lastUpdate
    def __str_c2l(self, s):
        return s.decode('utf8').encode(sys.stdin.encoding)
    def __str_l2c(self, s):
        try:
            return s.decode(sys.stdin.encoding).encode('utf8')
        except:
            return s.decode(chardet.detect(s)['encoding'] or 'utf8').encode('utf8')
    def read_note(self, noteFullPath):
        if os.path.exists(os.path.join(*[self.__str_c2l(p) for p in noteFullPath.split('/')])):
            noteFullPath += noteFullPath.split('/')[-1:]
        for postfix in ('.md', '.txt'):
            if os.path.exists(os.path.join(*[self.__str_c2l(p) for p in (noteFullPath+postfix).split('/')])):
                noteFullPath += postfix
                isMd = postfix == '.md'
                break
        else:
            return None, False
        with open(os.path.join(*[self.__str_c2l(p) for p in noteFullPath.split('/')])) as f: r = f.read()
        try:
            r.decode('utf8')
            return r, isMd
        except:
            try:
                return r.decode(chardet.detect(r)).encode('utf8'), isMd
            except:
                return None, False
    def write_note(self, noteFullPath, contentDict = {}):
        if '/' in noteFullPath:
            nbName, nName = self.__str_c2l(noteFullPath).split('/')
            # clear environment
            if os.path.exists(nbName):
                for postfix in ('.md', '.txt'):
                    if os.path.exists(os.path.join(nbName, nName+postfix)): os.remove(os.path.join(nbName, nName+postfix))
                if os.path.exists(os.path.join(nbName, nName)):
                    for fName in os.walk(os.path.join(nbName, nName)).next()[2]:
                        os.remove(os.path.join(nbName, nName, fName))
                    os.rmdir(os.path.join(nbName, nName))
            else:
                os.mkdir(nbName)
            # download files
            if not contentDict:
                pass
            elif len(contentDict) == 1:
                for k, v in contentDict.items():
                    self.write_file(noteFullPath, v, os.path.splitext(k)[1])
            else:
                if not os.path.exists(os.path.join(nbName, nName)): os.mkdir(os.path.join(nbName, nName))
                for k, v in contentDict.iteritems():
                    self.write_file(noteFullPath+'/'+k, v, '') # ok, this looks strange
        else:
            if contentDict: # create folder
                if not os.path.exists(self.__str_c2l(noteFullPath)): os.mkdir(self.__str_c2l(noteFullPath))
            else: # delete folder
                noteFullPath = self.__str_c2l(noteFullPath)
                if os.path.exists(noteFullPath):
                    for fName in os.walk(noteFullPath).next()[2]:
                        os.remove(os.path.join(noteFullPath, fName))
                    for fName in os.walk(noteFullPath).next()[1]:
                        for dName in os.walk(noteFullPath, fName).next()[2]:
                            os.remove(os.path.join(noteFullPath, fName, dName))
                        os.rmdir(os.path.join(noteFullPath, fName))
                    os.rmdir(noteFullPath)
    def write_file(self, noteFullPath, content, postfix = '.md'):
        if len(noteFullPath.split('/')) < 1: return False
        if not os.path.exists(self.__str_c2l(noteFullPath.split('/')[0])):
            os.mkdir(self.__str_c2l(noteFullPath.split('/')[0]))
        try:
            noteFullPath += postfix
            with open(self.__str_c2l(os.path.join(*noteFullPath.split('/'))), 'wb') as f: f.write(content)
            return True
        except:
            return False
    def get_file_dict(self):
        fileDict = {}
        for nbName in os.walk('.').next()[1]: # get folders
            nbNameUtf8 = self.__str_l2c(nbName)
            fileDict[nbNameUtf8] = []
            for nName in reduce(lambda x,y: x+y, os.walk(nbName).next()[1:]): # get folders and files
                filePath = os.path.join(nbName, nName)
                if os.path.isdir(nName):
                    fileDict[nbNameUtf8].append((self.__str_l2c(nName), os.stat(filePath).st_mtime))
                else:
                    fileDict[nbNameUtf8].append((self.__str_l2c(os.path.splitext(nName)[0]), os.stat(filePath).st_mtime))
        return fileDict