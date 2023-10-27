import threading,time,re,requests
from terminal_quick.terminal import Terminal

# 线程标志位(标志位并不能及时停止线程，只是用于通知线程停止)
start=True

# 应用id可以在steam商店页面找到
app_id=322330

# Workshop官网
url="https://steamcommunity.com/sharedfiles/filedetails/?id="

# 需要定期更新的mod列表
mods=[
    '3032865114'
]

# 通过mod_id获取数据库中的版本号
def get_version(mod_id):
    pass

# 通过mod_id和下载文件的路径更新数据库数据
def update(mod_id,path):
    # 通过lua解析mod的配置文件
    # 将解析出来的数据更新到数据库
    # 通过某种方法获取mod的版本号
    pass

class MyTerminal(Terminal):

    def _handle(self,data:str)->None:
        # 不换行输出
        print(data,end='')
        # 通过正则表达式获取正在下载的mod的id
        mod_id=re.search(r'Downloading\sitem\s(\d+)\s...',data)
        if mod_id:
            mod_id=mod_id.group(1)
            print(f'检测到mod {mod_id} 正在下载')
        # 通过正则表达式获取成功下载的mod的id和路径
        mod_info=re.search(r'Success.\sDownloaded\sitem\s(\d+)\sto\s"([\/a-zA-Z0-9 _]+)"',data)
        if mod_info:
            mod_id,mod_path=mod_info.group(1),mod_info.group(2)
            print(f'检测到mod {mod_id} 下载完成，路径为 {mod_path}')
        """
        请在这里添加你的代码
        """

# 启动steamcmd
terminal=MyTerminal('/root/steamcmd/steamcmd.sh')
# # 匿名登录steam
terminal.write(f'login anonymous\r')
# 开启一个定时任务，每隔一段时间检查一次mod是否需要更新
def check_mods():
    global mods,terminal,url,start
    print('检查mod是否需要更新的线程已启动')
    count=3600
    while start:
        if count>=3600:
            count=0
            print('正在检查mod是否需要更新')
            for mod in mods:
                print(f'正在检查mod {mod} 是否需要更新')
                try:
                    workshop_url=url+str(mod)
                    # 获取mod的html页面
                    html=requests.get(workshop_url,timeout=15).text
                    # 通过正则表达式获取mod的版本号
                    version=re.search(r'<span class="workshopTagsTitle">.*?version:([\d\.]+)</a></div>',html)
                    if version:
                        version=version.group(1)
                        print(f'检测到mod {mod} 的版本号为 {version}')
                        # 请在这里判断mod的版本号是否需要更新，如果需要更新则执行下面的代码
                        """
                        请在这里添加你的代码
                        """
                        terminal.write(f'workshop_download_item {app_id} {mod}\r')
                        print(f'正在尝试更新mod {mod}')
                    else:
                        print(f'检测到mod {mod} 的版本号获取失败')
                except requests.RequestException as e:
                    print(f'检测mod {mod} 是否需要更新时出现异常 {e}')
                if not start:
                    break
                time.sleep(10)
        if not start:
            break
        count+=1
        time.sleep(1)
    print('检查mod是否需要更新的线程已退出')

def user_input():
    global terminal,start
    while True:
        input_=input()
        if input_=='exit':
            print('正在尝试退出程序')
            # 退出多线程
            start=False
            # 退出steamcmd
            terminal.stop()
            break
        input_+='\r'
        terminal.write(input_)
    print('程序已退出')

# 开启一个线程用于定期检查mod是否需要更新
threading.Thread(target=check_mods).start()

# 开启一个线程用于监听用户输入
threading.Thread(target=user_input).start()