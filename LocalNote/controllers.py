import os, time

from local.storage import Storage as LocalStorage
from evernoteapi.storage import Storage as EvernoteStorage
from evernoteapi.controller import EvernoteController

class Controller(object):
    def __init__(self):
        self.ls = LocalStorage()
        self.es = EvernoteStorage()
        self.token, self.isSpecialToken, self.sandbox, self.isInternational, self.expireTime, self.lastUpdate = self.ls.get_config()
        self.available, self.ec = self.__check_available()
        self.changesList = []
    def __check_available(self):
        if not self.isSpecialToken and self.expireTime < time.time(): return False, None
        if self.token == '': return False, None
        try:
            ec = EvernoteController(self.token, self.isSpecialToken, self.sandbox, self.isInternational)
            self.ls.update_config(self.token, self.isSpecialToken, self.sandbox, self.isInternational, self.expireTime, self.lastUpdate)
            self.es.update(self.token, ec.noteStore)
            return True, ec
        except:
            return False, None
    def log_in(self, interAct = True, config = {}):
        if interAct:
            pass
        else:
            if config.get('token') is not None: self.token = config.get('token')
            if config.get('isSpecialToken') is not None: self.isSpecialToken = config.get('isSpecialToken')
            if config.get('sandbox') is not None: self.sandbox = config.get('sandbox')
            if config.get('isInternational') is not None: self.isInternational = config.get('isInternational')
            if config.get('expireTime') is not None: self.expireTime = config.get('expireTime')
            if config.get('lastUpdate') is not None: self.lastUpdate = config.get('lastUpdate')
        available, ec = self.__check_available()
        if available:
            self.available = True
            self.ec = ec
        return available
    def fetch_notes(self):
        if self.available: return False
        self.ec.storage.update(self.token, self.ec.noteStore)
        return True
    def __get_changes(self, update = False): # -1 for need download, 1 for need upload, 0 for can be uploaded and downloaded
        if not update: return self.changesList # (fileFullPath, status)
        r = []
        fileDict = self.ls.get_file_dict()
        noteDict = self.es.get_note_dict()
        for nbName, lNotes in fileDict.items():
            eNotes = noteDict.get(nbName)
            if eNotes is None: # notebook exists locally not online
                r.append((nbName, 0))
                continue
            delIndex = []
            for lNote in lNotes:
                for i, eNote in enumerate(eNotes):
                    if lNote[0] != eNote[0]: continue
                    if self.ls.lastUpdate < lNote[1]: # need upload
                        if self.ls.lastUpdate < eNote[1]: # need download
                            r.append((nbName+'/'+lNote[0], 0))
                        else:
                            r.append((nbName+'/'+lNote[0], 1))
                    else:
                        if self.ls.lastUpdate < eNote[1]:
                            r.append((nbName+'/'+lNote[0], -1))
                        else:
                            # debug
                            r.append((nbName+'/'+lNote[0], 2))
                    delIndex.append(i)
                    break
                else: # note exists locally not online
                    r.append((nbName+'/'+lNote[0], 0))
            eNotes = [n for i, n in enumerate(eNotes) if i not in delIndex]
            for eNote in eNotes: r.append((nbName+'/'+eNote[0], 0)) # note exists online not locally
            del noteDict[nbName]
        for nbName in noteDict.keys(): r.append((nbName, 0))
        self.changesList = r
        return r
    # DEBUG
    def get_changes(self):
        return self.__get_changes(True)
    def download_notes(self, update = True):
        if not self.available: return False
        noteDict = self.es.get_note_dict()
        def _download_note(noteFullPath):
            print(('Downloading '+noteFullPath).decode('utf8'))
            if self.es.get(noteFullPath) is None: # delete note if is deleted online
                self.ls.write_note(noteFullPath, {})
                return
            contentDict = self.ec.get_attachment(noteFullPath)
            if contentDict.get(noteFullPath.split('/')[1]+'.md') is None:
                if contentDict.get(noteFullPath.split('/')[1]+'.txt') is None:
                    contentDict[noteFullPath.split('/')[1]+'.txt'] = self.ec.get_content(noteFullPath)
                else: # avoid mistaken overwrite of attachment
                    fileNum = 1
                    while 1:
                        if contentDict.get(noteFullPath.split('/')[1]+'(%s).txt'%fileNum) is None:
                            contentDict[noteFullPath.split('/')[1]+'(%s).txt'%fileNum] = contentDict[noteFullPath.split('/')[1]+'.txt']
                            contentDict[noteFullPath.split('/')[1]+'.txt'] = self.ec.get_content(noteFullPath)
                            break
                        else:
                            fileNum += 1
            self.ls.write_note(noteFullPath, contentDict)
        for noteFullPath, status in self.__get_changes(update):
            if status not in (-1, 0): continue
            if '/' in noteFullPath:
                _download_note(noteFullPath)
            else:
                notes = noteDict.get(noteFullPath)
                if notes is None:
                    self.ls.write_note(noteFullPath, {}) # delete folder
                else:
                    self.ls.write_note(noteFullPath, {1}) # create folder
                    for note in notes: _download_note(noteFullPath+'/'+note[0])
        self.ls.update_config(lastUpdate = time.time())
        return True
    def upload_file(self, update = True):
        if not self.available: return False
        noteDict = self.es.get_note_dict()
        for fileFullPath, status in self.__get_changes(update):
            if status not in (1, 0): continue
            if '/' in fileFullPath:
                nbName, nName = fileFullPath.split('/')
                for postfix in ('.md', '.txt', ''):
                    content = get_file(fileFullPath + '.md')
                    if content is None: continue
                    if postfix == '.md':
                        self.ec.update_note(fileFullPath, content, os.path.join(nbName, nName+'.md'))
                    else:
                        self.ec.update_note(fileFullPath, content)
                else:
                    self.ec.delete_note(fileFullPath)
            else:
                if os.path.exists(fileFullPath):
                    self.ec.create_notebook(fileFullPath)
                    for note in self.ls.get_file_dict()[fileFullPath]:
                        content, isMd = self.ls.get_file(fileFullPath+'/'+note[0])
                        self.ec.update_note(fileFullPath+'/'+note[0], content, fileFullPath+'/'+note[0] if isMd else None)
                else:
                    self.ec.delete_notebook(fileFullPath)
        self.__get_changes(update = True)
        return True

def __check_file(self, noteName, notebookName, note):
    # -1 for need download, 1 for need upload, 0 for can be uploaded and downloaded, 2 for updated
    if os.path.exists(self.__str_c2l(os.path.join(notebookName, noteName + '.md'))):
        fileDir = self.__str_c2l(os.path.join(notebookName, noteName + '.md'))
    elif os.path.exists(os.path.join(notebookName, noteName + '.txt')):
        fileDir = self.__str_c2l(os.path.join(notebookName, noteName + '.txt'))
    else:
        return -1
    if self.lastUpdate < note.updated / 1000:
        if self.lastUpdate < os.stat(fileDir).st_mtime:
            return 0
        else:
            return -1
    else:
        if self.lastUpdate < os.stat(fileDir).st_mtime:
            return 1
        else:
            return 2