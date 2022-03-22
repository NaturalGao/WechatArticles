# coding: utf-8
import urllib.parse
from tkinter import *
import tkinter as tk
import tkinter.messagebox as MessageBox
import tkinter.ttk as TTK
import threading
import pyperclip
import base64
from GetUrls import *
from Calendar import Calendar


def thread_it(func, *args):
    '''将函数打包进线程'''
    # 创建
    t = threading.Thread(target=func, args=args)
    # 守护 !!!
    t.setDaemon(True)
    # 启动
    t.start()


# 爬取文章信息
def slidePosts(data, test, date_start_val, date_end_val):
    print(data)
    global max_post_count, progressbarRadio, model_value, post_count

    date_start_val = time.mktime(time.strptime(date_start_val, "%Y-%m-%d"))
    date_end_val = time.mktime(time.strptime(date_end_val, "%Y-%m-%d"))

    # 选择的模式  1 全部  2头二条
    radio_model_value = model_value.get()
    # 重构的数据
    url_title_lst = []
    for i, line in enumerate(data, 0):
        print("index:", i)
        # item = json.loads('{' + line + '}', strict=False)
        for k, item in enumerate(line, 0):
            timestamp = item["comm_msg_info"]["datetime"]
            ymd = time.localtime(timestamp)
            date = '{}-{}-{}'.format(ymd.tm_year, ymd.tm_mon, ymd.tm_mday)
            print(date)
            if date_start_val <= timestamp <= date_end_val:
                infos = item['app_msg_ext_info']

                if infos['content_url'] and infos['title'] and (post_count < max_post_count or max_post_count == 0):
                    url_title_lst += [[infos['title'], infos['content_url'], date]]
                    post_count += 1

                if 'multi_app_msg_item_list' in infos.keys():
                    # for y, info in infos['multi_app_msg_item_list']:
                    #     if (radio_model_value == 2 and y >= 1) or (post_count >= max_post_count > 0):
                    #         break
                    #     url_title_lst += [info['title'], [info['content_url'], date]]
                    #     post_count += 1
                    for y, info in enumerate(infos['multi_app_msg_item_list'], 0):
                        if post_count >= max_post_count > 0:
                            break
                        url_title_lst += [[info['title'], info['content_url'], date]]
                        post_count += 1
                if post_count >= max_post_count > 0:
                    break
        if post_count >= max_post_count > 0:
            break

    print(url_title_lst)
    print('文章结构重组完毕,开始获取访问量和点赞量')
    item_lst = []
    current_count = 0
    for title, url, date in url_title_lst:
        try:
            if not verify_url(url):
                continue
            # 获取文章阅读数在看点赞数
            read_num, like_num, old_like_num = test.read_like_nums(url)
            print(read_num, like_num, old_like_num)
            item_lst.append(
                [title, url, date, read_num, like_num])

            current_count += 1
            progressbar['value'] = (current_count / max_post_count) * 80
            progressbarRadio = round(progressbar['value'], 2)
            window.update_idletasks()
            time.sleep(random.randint(5, 10))

        except Exception as e:
            MessageBox.showinfo("温馨提示", "爬取失败，请检查是否关闭代理服务器！")
            break
        finally:
            print('获取文章阅读数在看点赞数')

    return item_lst


def deleteTree():
    x = treeview.get_children()
    for item in x:
        treeview.delete(item)
    return True


# 获取列表的第二个元素
def takeSecond(elem):
    return elem[3]


# 重置状态
def resetStatus():
    global loading, post_count
    # 重置进度条
    progressbar['value'] = 0
    window.update_idletasks()
    # 重置爬取状态
    loading = False
    # 重置已爬取数量
    post_count = 0
    return False

# 验证时间
def getDateTime():
    global date_start, date_end
    # 开始日期
    date_start_val = date_start.get()
    # 结束日期
    date_end_val = date_end.get()
    try:
        time.strptime(date_start_val, "%Y-%m-%d")
        time.strptime(date_end_val, "%Y-%m-%d")
    except:
        raise Exception('日期格式有误，请重新输入！')

    if date_start_val > date_end_val:
        raise Exception('开始日期不能“大于”截至日期')

    return date_start_val, date_end_val

# 开始获取文章
def startCallBack():
    global loading, T1
    # 密钥
    secret_key = T1.get("0.0", "end")

    if len(secret_key) == 1:
        MessageBox.showinfo("温馨提示", "请输入密钥!")
        return False

    # 获取开始日期 和 截至日期
    try:
        date_start_val, date_end_val = getDateTime()
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        MessageBox.showinfo("温馨提示", exc_value)
        return False

    if loading is True:
        MessageBox.showinfo("温馨提示", "已经在爬取~")
        return False

    loading = True

    secret_key_decode = base64.b64decode(secret_key)

    secret_key_decode = str(secret_key_decode, "utf-8")
    secret_key_decode = secret_key_decode.split('&')

    params = {}
    for i, item_secret_key in enumerate(secret_key_decode, 0):
        key_value = item_secret_key.split('=')
        if (len(key_value) > 2):
            __val = key_value[1]
            for k in range(2, len(key_value)):
                __val += '='
            key_value[1] = __val

        if (key_value[0] != 'cookie'):
            params[key_value[0]] = key_value[1]
        else:
            cookie_val = item_secret_key.split('=', 1)
            params[cookie_val[0]] = cookie_val[1]

    params['__biz'] = urllib.parse.unquote(params['__biz'])
    params['appmsg_token'] = urllib.parse.unquote(params['appmsg_token'])

    appmsg_token = params['appmsg_token']
    biz = params['__biz']
    uin = params['uin']
    cookie = params['cookie']
    key = params['key']

    try:
        # 文章
        data = method_one(biz, uin, cookie, key)
        # # 获取点赞数、阅读数、评论信息
        test = ArticlesInfo(appmsg_token, cookie)
        deleteTree()
        # 需要插入的数据
        item_lst = slidePosts(data, test, date_start_val, date_end_val)
        # 按阅读量降序
        item_lst.sort(key=takeSecond, reverse=True)
        # 插入表格
        insertTreeview(item_lst)
        MessageBox.showinfo("温馨提示", "爬取成功！")
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(exc_value)
        MessageBox.showinfo("警告", "密钥已过期，请更换新的密钥尝试!")

    # 重置状态
    resetStatus()
    return True


def insertTreeview(item_lst):
    global max_post_count, progressbarRadio
    current_count = 0
    for title, url, logo, date, read_num, like_num in item_lst:
        current_count += 1
        progressbar['value'] += (current_count / max_post_count) * 20
        progressbarRadio = round(progressbar['value'], 2)
        window.update_idletasks()

        treeview.insert('', current_count, values=(current_count, title, url, date, read_num, like_num))

    return True


def __intTable():
    treeview.column("序号", width=20, anchor='center')
    treeview.column("文章标题", width=100, anchor='center')  # 表示列,不显示
    treeview.column("URL地址", width=300, anchor='center')
    treeview.column("日期", width=50, anchor='center')
    treeview.column("阅读量", width=50, anchor='center')  # 表示列,不显示
    treeview.column("点赞量", width=50, anchor='center')

    treeview.heading("序号", text="序号")
    treeview.heading("文章标题", text="文章标题")
    treeview.heading("URL地址", text="URL地址")
    treeview.heading("日期", text="日期")
    treeview.heading("阅读量", text="阅读量")
    treeview.heading("点赞量", text="点赞量")
    treeview.bind('<Double-Button-1>', treeviewClick)  # 绑定双击离开事件===========


# 双击复制文章URL
def treeviewClick(event):
    for item in treeview.selection():
        item_text = treeview.item(item, "values")
        pyperclip.copy(item_text[2])
        MessageBox.showinfo("温馨提示", "文章URL复制成功~")


if __name__ == '__main__':
    # 白名单
    fillField = ['__biz', 'uin', 'key', 'appmsg_token', 'cookie']
    # 文章默认爬取数量
    max_post_count = 50
    # 当前已爬取数量
    post_count = 0

    loading = False
    window = Tk()
    # 第2步，给窗口的可视化起名字
    window.title('公众号文章助手')
    window.iconbitmap("favicon.ico")

    width, height = 1024, 768  # 窗口大小
    x, y = (window.winfo_screenwidth() - width) / 2, (window.winfo_screenheight() - height) / 2
    window.geometry('%dx%d+%d+%d' % (width, height, x, y))  # 窗口位置居中

    m1 = PanedWindow(orient=VERTICAL)  # 默认是左右分布的
    m1.pack(fill=BOTH, expand=1)

    m2 = PanedWindow(m1)  # 默认是左右分布的
    m1.add(m2)

    L1 = Label(m2, text='密钥', width=10)
    m2.add(L1)

    T1 = Text(m1, height=5)
    m2.add(T1)

    m3 = PanedWindow(m1)  # 默认是左右分布的
    m1.add(m3)

    hi_there = Button(m3, text="开始爬取", command=lambda: thread_it(startCallBack))
    m3.add(hi_there)

    m5 = PanedWindow(m1)  # 默认是左右分布的
    m1.add(m5)
    # 开始日期按钮
    date_str_gain = lambda: [
        date_str_start.set(date)
        for date in [Calendar((x, y + 200), 'ur').selection()]
        if date]
    B2 = Button(m5, text='开始日期:', width=50, command=date_str_gain)
    m5.add(B2)

    # 开始日期输入框
    date_str_start = tk.StringVar()
    date_start = TTK.Entry(m5, textvariable=date_str_start)
    m5.add(date_start)

    m6 = PanedWindow(m1)  # 默认是左右分布的
    m1.add(m6)
    # 结束日期按钮
    date_str_gain = lambda: [
        date_str_end.set(date)
        for date in [Calendar((x, y + 200), 'ur').selection()]
        if date]
    B3 = Button(m6, text='截至日期:', width=50, command=date_str_gain)
    m6.add(B3)

    # 结束日期输入框
    date_str_end = tk.StringVar()
    date_end = TTK.Entry(m6, textvariable=date_str_end)
    m6.add(date_end)

    m7 = PanedWindow(m1)  # 选择区域
    m1.add(m7)

    model_label = Label(m7, text='模式', width=50)
    m7.add(model_label)

    model_value = tk.StringVar()
    model_value.set(1)
    r1 = Radiobutton(m7, text='全部', variable=model_value, value=1)
    m7.add(r1)

    r2 = Radiobutton(m7, text='头条、二条', variable=model_value, value=2)
    m7.add(r2)

    m4 = PanedWindow(m1)  # 默认是左右分布的
    m1.add(m4)

    columns = ("序号", "文章标题", "URL地址", "日期", "阅读量", "点赞量")
    treeview = TTK.Treeview(window, height=18, show="headings", columns=columns)  # 表格
    __intTable()
    m4.add(treeview)

    # 进度条
    frame1 = Frame(window)
    progressbar = TTK.Progressbar(frame1, orient="horizontal", length=300, mode="determinate")
    progressbar.pack(side=LEFT)

    progressbarRadio = '未开始'
    progressbarLabel = Label(frame1, text=progressbarRadio)
    progressbarLabel.pack(side=RIGHT)

    frame1.pack(padx=10, pady=10)

    # 进入消息循环
    window.mainloop()
