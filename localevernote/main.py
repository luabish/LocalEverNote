# coding=utf8
import getpass
import os
import sys

import localevernote
from controllers import Controller, convert_html
from evernoteapi.dev_token import TokenFetcher
from exception import main_wrapper

DEBUG = os.getenv('dev_debug', '')
if DEBUG:
    os.chdir(os.environ['test_dir'])


def sys_print(s, level='info'):
    print(('[%-4s] %s' % ((level + ' ' * 4)[:4].upper(), s.replace(u'\xa0', ' '))).encode(sys.stdin.encoding))


def sys_input(s):
    return raw_input(s.encode(sys.stdin.encoding)).decode(sys.stdin.encoding)


def check_files_format(fn):
    def _check_files_format(*args, **kwargs):
        mainController = Controller()
        configFound, wrongFiles = mainController.check_files_format()
        if not configFound:
            sys_print(u'检测到你不在印象笔记主目录中，或配置文件损坏', 'warn')
        elif mainController.available:
            if wrongFiles and not DEBUG:
                for fileName, status in wrongFiles:
                    if status == 1:
                        sys_print(u'检测到错误放置的内容：' + fileName.decode('utf8'), 'warn')
                    elif status == 2:
                        sys_print(u'检测到内容过大的文件：' + fileName.decode('utf8'), 'warn')
                    elif status == 3:
                        sys_print(u'检测到意义不明的文件：' + fileName.decode('utf8'), 'warn')
                sys_print(u'请确保单条笔记有md或html的正文且不大于%s字节' % mainController.ls.maxUpload)
                sys_print(u'请确保没有文件夹格式的附件，或名为.DS_Store的笔记及笔记本。')
            else:
                return fn(mainController, *args, **kwargs)
        elif mainController.ls.get_credential():
            u, p = mainController.ls.get_credential().split('|')
            _, _, sandbox, is_international, expire_time, _, _ = mainController.ls.get_config()
            token = TokenFetcher(is_international, u, p).fetch_token()
            if token:
                mainController.log_in(token=token, isSpecialToken=True, sandbox=sandbox,
                                      isInternational=is_international, expireTime=expire_time)
                if mainController.available:
                    mainController.ls.update_config(token=token, isSpecialToken=True,
                                                    sandbox=sandbox, isInternational=is_international,
                                                    expireTime=expire_time)
                    sys_print(u'刷新token成功')
                else:
                    sys_print(u'刷新token失败')
            else:
                sys_print(u'获取token失败，请检查用户名密码')
        else:
            sys_print(u'尚未初始化', 'warn')

    return _check_files_format


def show_help(*args):
    print('当前版本为：%s' % localevernote.__version__)
    for fn, h in argDict.iteritems():
        print('%-10s: %s' % (fn, h[1].decode('utf8').encode(sys.stdin.encoding)))


def init(*args):
    mainController = Controller()

    def _init(*args):
        if not reduce(lambda x, y: x + y, [l for l in os.walk('.').next()[1:]]):
            sys_print(u'账户仅需要在第一次使用时设置一次')
            while 1:
                product_type = sys_input(u'请选择版本[0]中国版印象笔记[1]国际版Evernote[2]中国版沙盒>')
                if product_type == '0':
                    is_international, is_sandbox = False, False
                elif product_type == '1':
                    sys_print(u'目前尚未支持国际版', 'error')
                    break
                elif product_type == '2':
                    is_international, is_sandbox = False, True
                else:
                    continue
                u = sys_input(u'登陆邮箱>')
                p = getpass.getpass()
                token = TokenFetcher(int(product_type), u, p).fetch_token()
                if token:
                    mainController.log_in(token=token, isSpecialToken=True, sandbox=is_sandbox,
                                          isInternational=is_international, expireTime=None)
                    if mainController.available:
                        mainController.ls.update_config(token=token, isSpecialToken=True,
                                                        sandbox=is_sandbox, isInternational=is_international,
                                                        expireTime=None)
                        sys_print(u'登陆成功')
                        mainController.ls.save_credential(u, p)
                        sys_print(u'保存用户身份成功')
                        break
                    else:
                        sys_print(u'登录失败')
                        if sys_input(u'重试登录？[yn] ') != 'y': break
                else:
                    sys_print(u'获取token失败,请检查用户名或密码')
                    if sys_input(u'重试登录？[yn] ') != 'y': break
        else:
            sys_print(u'目录非空，无法初始化', 'warn')
            return

    if mainController.available:
        if sys_input(u'已经登录，是否要重新登录？[yn] ') == 'y': _init(*args)
    else:
        _init(*args)
    print('Bye~')


def notebook(*args):
    mainController = Controller()
    notebooks = []
    sys_print(u'请输入使用的笔记本名字，留空结束')
    while 1:
        nb = sys_input(u'> ').encode('utf8')
        if nb:
            notebooks.append(nb)
        else:
            break
    if notebooks:
        mainController.ls.update_config(notebooks=notebooks)
        sys_print(u'修改成功')
    else:
        sys_print(u'未修改')
    print('Bye~')


@check_files_format
def config(mainController, *args):
    sys_print(u'目前登录用户： ' + mainController.ec.userStore.getUser().username)


@check_files_format
def pull(mainController, *args):
    mainController.fetch_notes()
    # show changes
    for change in mainController.get_changes():
        if change[1] in (-1, 0): sys_print('/'.join(change[0]).decode('utf8'), 'pull')
    # confirm
    if sys_input(u'是否更新本地文件？[yn] ') == 'y':
        r = mainController.download_notes(False)
        if isinstance(r, list):
            sys_print(u'为存储到本地，请确保笔记名字中没有特殊字符“\\/:*?"<>|”或特殊不可见字符')
            sys_print(u'为兼容Mac电脑，需要将名字为".DS_Store"的笔记本或笔记更名')
            for noteFullPath in r: sys_print('/'.join(noteFullPath).decode('utf8'))
    print('Bye~')


@check_files_format
def push(mainController, *args):
    mainController.fetch_notes()
    # show changes
    for change in mainController.get_changes():
        if change[1] in (1, 0): sys_print('/'.join(change[0]).decode('utf8'), 'push')
    # confirm
    if sys_input(u'是否上传本地文件？[yn] ') == 'y':
        mainController.upload_files(False)
    print('Bye~')


@check_files_format
def status(mainController, *args):
    mainController.fetch_notes()
    # show changes
    changes = mainController.get_changes()
    if changes:
        for change in changes:
            if change[1] == -1:
                sys_print('/'.join(change[0]).decode('utf8'), 'pull')
            elif change[1] == 1:
                sys_print('/'.join(change[0]).decode('utf8'), 'push')
            elif change[1] == 0:
                sys_print('/'.join(change[0]).decode('utf8'), 'both')
    else:
        sys_print(u'云端和本地笔记都处于已同步的最新状态。')


def convert(*args):
    if 0 < len(args):
        fileName, ext = os.path.splitext(args[0])
        if sys_input(u'将会生成：%s，是否继续？[yn] ' % (fileName.decode(sys.stdin.encoding) + '.md')) != 'y': return
        status = convert_html(args[0])
        if status in (1, 2, 4):
            if status == 1:
                sys_print(u'仅能转换html文件', 'warn')
            elif status == 2:
                sys_print(u'没有找到此文件', 'warn')
            else:
                sys_print(u'无法正常解码，请尝试Utf8编码')
            return
        else:
            if status == 3:
                if sys_input(u'已检测到同名.md文件，是否继续写入？[yn] ') != 'y':
                    return
                else:
                    status = convert_html(args[0],
                                          sys_input(u'是否覆盖写入，否将自动添加后缀[yn] ') == 'y')
            sys_print(u'已成功生成%s。' % status.decode(sys.stdin.encoding))
    else:
        sys_print(u'使用方式：localnote convert 需要转换的文件.html')


argDict = {
    'help': (show_help, '显示帮助'),
    'init': (init, '登陆localnote'),
    'notebook': (notebook, '设定使用指定的笔记本'),
    'config': (config, '查看已经登录的账户'),
    'pull': (pull, '下载云端笔记'),
    'push': (push, '上传本地笔记'),
    'status': (status, '查看本地及云端更改'),
    'convert': (convert, '将html文件转为markdown格式')
}


def main():
    del sys.argv[0]
    if not sys.argv: sys.argv.append('help')

    @main_wrapper
    def _main():
        argDict.get(sys.argv[0], (show_help,))[0](*sys.argv[1:])

    _main()


if __name__ == '__main__':
    main()
