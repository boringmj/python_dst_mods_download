import threading,time,re,json,ctypes
from terminal_quick.terminal import Terminal
# 请自行使用pip安装pymysql
import pymysql

"""
steamcmd下载的mod默认在启动用户的家目录下的Steam/steamapps/workshop/content/322330中
请注意完成下面的配置
本程序只会从数据库中读取status为0或1的mod

@ahthor: boringmj(wuliaodemoji@wuliaomj.com)
"""

# steamcmd路径(必须保证steamcmd已经安装且依赖已经安装)
steamcmd_path='~/steamcmd/steamcmd.sh'

# 数据库信息(默认使用uft8mb4编码，因为modinfo.lua中可能包含emoji表情)
db_config={
    'host':'localhost',
    'port':3306,
    'user':'user',
    'password':'pass',
    'database':'database'
}

# 休眠时间(单位：秒,如果时间过短可能会导致上一个队列还未处理完就加入了新的队列,导致队列长度逐渐增加)
sleep_time=60*60

# 线程标志位(标志位并不能及时停止线程，只是用于通知线程停止)
start=True

# 应用id可以在steam商店页面找到
app_id=322330

# 预先处理
ll=ctypes.cdll.LoadLibrary
dll=ll("./luatool.so")
get_modinfo=dll.GetModInfo
get_modinfo.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int]
get_modinfo.restype=None
buffer_size=1024*10


# 连接数据库
db=pymysql.connect(
    host=db_config['host'],
    port=db_config['port'],
    user=db_config['user'],
    password=db_config['password'],
    database=db_config['database'],
    charset='utf8mb4'
)

class MyTerminal(Terminal):

    def _handle(self,data:str)->None:
        global dll,buffer_size
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
            try:
                output_buffer=ctypes.create_string_buffer(buffer_size)
                dll.GetModInfo(bytes(mod_path+"/modinfo.lua",encoding="utf-8"),output_buffer,len(output_buffer))
                # print(output_buffer.value.decode("utf-8"))
                # 获取mod的信息
                mod_info=json.loads(output_buffer.value.decode("utf-8"))
                # 写入数据库
                cursor=db.cursor()
                cursor.execute('update `ssd_mod_info` set `mod_path`=%s,`status`=1,`name`=%s,`version`=%s,`author`=%s,`description`=%s,`configuration_options`=%s where `mod_id`=%s',(mod_path,mod_info['name'],mod_info['version'],mod_info['author'],mod_info['description'],json.dumps(mod_info['configuration_options']),mod_id))
                db.commit()
                cursor.close()
                print(f'mod {mod_id} 已更新到数据库')
            except Exception as e:
                print(f'更新mod {mod_id} 时发生错误：{e}')

# 启动steamcmd
terminal=MyTerminal(steamcmd_path)
# # 匿名登录steam
terminal.write(f'login anonymous\r')
# 开启一个定时任务，每隔一段时间检查一次mod是否需要更新
def check_mods():
    global terminal,start,db,sleep_time
    print('检查mod是否需要更新的线程已启动')
    count=sleep_time
    while start:
        if count>=sleep_time:
            count=0
            print('正在尝试加载mod列表')
            # 获取mod列表
            cursor=db.cursor()
            cursor.execute('select `mod_id`,`version` from `ssd_mod_info` where `status` in (0,1)')
            mods=cursor.fetchall()
            cursor.close()
            print('mod列表加载完成')
            # 通过steamcmd更新mod
            for mod in mods:
                mod_id,version=mod
                # 检查mod是否需要更新
                print(f'正在检查mod {mod_id}: {version} 是否需要更新')
                terminal.write(f'workshop_download_item {app_id} {mod_id}\r')
                if not start:
                    break
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
            # 关闭数据库连接
            db.close()
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