from asyncio import proactor_events
import logging
import time
import threading
import heapq

__all__ = ['ProxyManager', 'HttpProxy']

# Http代理
# 支持设置生命周期，超过生命周期后会被删除，不会被再次使用
class HttpProxy:
    # ip
    _ip: str
    # 端口
    _port: int

    # 最大使用量
    _maxUseCount: int = -1
    # 使用量
    _useCount: int = 0

    # 生命周期，单位为秒，-1表示不限制生命周期，默认为-1
    _lifeTime: int = -1
    # 开始时间，单位为秒，-1表示未开始，默认为-1
    _startTime: int = -1

    # 是否取消使用
    _isCancelUse: bool = False
    
    # 类初始化
    def __init__(self, ip: str, port: int):
        self._ip = ip
        self._port = port
    
    # 大小比较 
    def __lt__(self, other):
        return self._useCount < other._useCount

    # 设置生命周期
    def setLifeTime(self, lifeTime: int):
        self._lifeTime = lifeTime
        self._startTime = time.time()

    # 设置最大使用量
    def setMaxUseCount(self, maxUseCount: int):
        self._maxUseCount = maxUseCount

    # 是否满负载
    def isFullUse(self) -> bool:
        if self._maxUseCount == -1: return False
        return self._useCount >= self._maxUseCount

    # 是否没有在使用
    def isNoUse(self) -> bool:
        return self._useCount == 0

    # 使用
    def use(self) -> bool:
        if not self.isFullUse():
            self._useCount += 1
            return True
        return False

    # 归还
    def useReturn(self):
        self._useCount -= 1
        if self._useCount < 0: self._useCount = 0

    # 是否过期
    def isExpired(self) -> bool:
        if self._lifeTime == -1: return False
        return time.time() - self._startTime > self._lifeTime

    # 设置取消使用
    def setCanceled(self):
        self._isCancelUse = True

    # 是否取消使用
    def isCanceled(self) -> bool:
        return self._isCancelUse

    def proxies(self):
        pro = "://%(ip)s:%(port)s" % {"ip" : self._ip,"port" : self._port}
        return {"http": 'http' + pro, "https": 'http' + pro}

    def __str__(self):
        return self._ip + ":" + str(self._port)

class ProxyManager:
    # 代理列表
    _proxies: list[HttpProxy] = []
    # 代理池容量
    _proxyPoolCapacity: int = -1
    # 现有代理数量
    _proxyPoolSize: int = 0
    # 归还事件
    _returnEvent: threading.Event = threading.Event()
    # 获取代理函数 
    _getProxyFunc: callable = None

    # 类初始化
    def __init__(self, proxyPoolCapacity, getProxyFunc: callable = None):
        self._proxyPoolCapacity = proxyPoolCapacity
        self._getProxyFunc = getProxyFunc

    # 初始化
    def init(self):
        if self._proxyPoolCapacity <= 0:
            logging.error("ProxyManager init error: proxyPoolCapacity must be greater than 0")
            return None
        if self._getProxyFunc is None:
            logging.error("ProxyManager init error: getProxyFunc must be not None")
            return None
        for i in range(self._proxyPoolCapacity):
            while (proxy := self._getProxyFunc()) is None: pass
            heapq.heappush(self._proxies, proxy)
            self._proxyPoolSize += 1
        return self
    
    # 设置获取代理函数
    def setGetProxyFunc(self, getProxyFunc: callable):
        self._getProxyFunc = getProxyFunc
    
    # 获取Http代理
    def getHttpProxy(self) -> HttpProxy:
        if self._proxyPoolSize == 0:
            logging.warning("proxyPool run out, waiting")
            self._returnEvent.wait()
            logging.warning("proxyPool waiting end")
        self._returnEvent.clear()
        proxy = self.isExpiredAndGetNew(heapq.heappop(self._proxies))
        proxy.use()
        if proxy.isFullUse():
            self._proxyPoolSize -= 1
        heapq.heappush(self._proxies, proxy)
        return proxy 

    # 归还Http代理
    def returnHttpProxy(self, proxy: HttpProxy):
        if self.checkProxyDeleted(proxy): return
        if proxy.isFullUse():
            self._proxyPoolSize += 1
        proxy.useReturn()
        heapq.heapify(self._proxies)
        self._returnEvent.set()

    def deleteProxy(self, proxy: HttpProxy):
        proxy.setCanceled()
        self._proxies.remove(proxy)
        while (proxy := self._getProxyFunc()) is None: pass
        self._proxies.append(proxy)
        heapq.heapify(self._proxies)

    def checkProxyDeleted(self, proxy: HttpProxy):
        if not proxy.isCanceled(): return False
        if proxy.isNoUse():
            del proxy
            return True
        proxy.useReturn()
        return True            

    # 代理是否过期
    # 如果是, 则获取新代理并返回
    # 如果不是, 则返回原代理
    def isExpiredAndGetNew(self, proxy: HttpProxy) -> HttpProxy:
        if proxy is None or proxy.isExpired():
            while (newProxy := self._getProxyFunc()) is None: pass
            return newProxy
        return proxy