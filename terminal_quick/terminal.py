import threading,os
from abc import ABC,abstractmethod

class Terminal(ABC):
    """
    终端抽象类
    请注意实现 `_handle(self,data:str)->None` 方法

    @abstract method: _handle(self,data:str)->None 命令行输出监听
    @param command: 启动命令
    @param size: 单次读取的最大字节数
    @param code: 编码
    """

    def __init__(self,command:str,size:int=1024,code:str='utf-8')->None:
        """
        @param command: 启动命令
        @param size: 单次读取的最大字节数
        @param code: 编码
        """
        self._command=command
        self._size=size
        self._code=code
        self._run()
    
    def _run(self) -> None:
        """启动服务"""
        self._start=True
        self._pid,self._fd = os.forkpty() # type: ignore
        # 开启一个多线程用于循环读取
        if self._pid == 0:
            os.execvp(self._command.split(' ')[0],self._command.split(' '))
        else:
            self._thread=threading.Thread(target=self._read,daemon=True)
            self._thread.start()

    def write(self,content:str)->None:
        """写入终端(如需回车请自行添加)"""
        os.write(self._fd, content.encode(self._code))

    def _read(self)->None:
        """读取终端"""
        try:
            while self._start:
                data=os.read(self._fd,self._size).decode(self._code)
                if data:
                    self._handle(data)
        except OSError:
            print('终端已关闭')
    
    def stop(self)->None:
        """停止服务"""
        try:
            self._start=False
            os.close(self._fd)
            os.kill(self._pid,9)
        except OSError:
            pass

    @abstractmethod
    def _handle(self,data:str)->None:
        pass