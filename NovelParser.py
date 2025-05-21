from enum import Enum
import logging
import re
import os
import requests
from ProxyManager import HttpProxy, ProxyManager

__all__ = ['NovelParser', 'BookInfo', 'Chapter', 'BookStatus']

# 书籍连载状态
class BookStatus(Enum):
    # 未知
    unknown = 0
    # 连载中
    serializing = 1
    # 已完结
    completed = 2

# 书籍信息
class BookInfo:
    # 书籍网址
    url: str = None
    # 书名
    title: str = None
    # 作者
    author: str = None
    # 书籍连载状态
    status: BookStatus = BookStatus.unknown

    def __str__(self):
        return self.title + "|" + self.author + "|" + self.status.name

# 章节信息
class Chapter:
    # 章节名
    title: str
    # 章节号
    no: int
    # 章节网址
    url: str
    # 章节内容
    _content: str = None

    # 设置章节内容
    def setContent(self, content: str):
        self._content = content

    # 获取章节内容 
    def getContent(self) -> str | None:
        if self.content is None:
            logging.error("When " + self + " getContent, the content is None. You need call Parser.initChapter first")
        return self.content

    def __str__(self):
        return str(self.no) + ":" + self.title

 # 获取域名
def get_host_url(url: str) -> str | None:
    pattern = r'^(https?://[^/]+)'
    match = re.match(pattern, url)
    if match:return match.group(1)
    else: return None

# 默认线程池大小
__DEFAULT_THREAD_POOL_WORKER__ = 10
# 默认重试次数
__DEFAULT_CONNECT_RETRY_TIMES__ = 3
# 默认连接超时时间
__DEFAULT_CONNECT_TIMEOUT__ = 5
# 默认读取超时时间
__DEFAULT_READ_TIMEOUT__ = 15
class NovelParser:
    # 线程池大小
    _thread_pool_workers: int = __DEFAULT_THREAD_POOL_WORKER__

    # 重试次数
    _connect_retry_times: int = __DEFAULT_CONNECT_RETRY_TIMES__
    # 连接超时时间
    _connect_timeout: int = __DEFAULT_CONNECT_TIMEOUT__
    # 读取超时时间
    _read_timeout: int = __DEFAULT_READ_TIMEOUT__

    # 根据网址获取对应解析器
    @classmethod
    def getParser(cls, url):
        for file in os.listdir(os.path.join(os.path.dirname(__file__), "parsers")):
            if file.endswith(".py") and file != "__init__.py":
                module = __import__(f"parsers.{file[:-3]}", fromlist=[file[:-3]])
                cls = getattr(module, 'Parser')
                if get_host_url(cls._base_host_url) == get_host_url(url):
                    return cls(url)
                del module
    
    _proxyManager: ProxyManager = None
    _enableProxy: bool = False

    # 设置代理
    def setProxyManager(self, proxyManager:ProxyManager ):
        self._proxyManager = proxyManager
        self._enableProxy = True if proxyManager is not None else False

    # 网站域名
    _base_host_url: str = None

    # 书籍信息
    _book_info: BookInfo = BookInfo()
    # 章节列表
    _chapters: list[Chapter] = None   

    # 类初始化
    def __init__(self, url) -> None:
        self._book_info.url = url

    # 初始化
    def init(self):
        # 请求并解析主页
        self._parse_index(self._request_index())

    # get请求 
    def _get(self, url: str, errorMsg: str = None):
        html = None
        if self._enableProxy:
            html = self._doGetWithProxyManager(url, self._proxyManager)
        else:
            html = self._doGet(url)
        if html is not None: return html
        logging.error(errorMsg)
        return None

    def _doGetWithProxyManager(self, url: str, proxyManager: ProxyManager):
        proxy = proxyManager.getHttpProxy()
        html = self._doGetWithProxy(url, proxy)
        proxyManager.returnHttpProxy(proxy)

        if html is not None: return html
        
        proxyManager.deleteProxy(proxy)
        proxy = proxyManager.getHttpProxy()
        html = self._doGetWithProxy(url, proxy)
        proxyManager.returnHttpProxy(proxy)

        if html is not None: return html
        proxyManager.deleteProxy(proxy)
        return None

    def _doGetWithProxy(self, url: str, proxy: HttpProxy):
        i = 0
        while i < self._connect_retry_times:
            try:
                logging.debug(f"{proxy._ip}:{proxy._port} {url}")
                html = requests.get(url, proxies=proxy.proxies(), timeout=(self._connect_timeout, self._read_timeout)).text
                return html
            except requests.exceptions.RequestException:
                logging.debug("retry " + url)
                i += 1
        return None

    def _doGet(self, url: str):
        i = 0
        while i < self._connect_retry_times:
            try:
                html = requests.get(url, timeout=(self._connect_timeout, self._read_timeout)).text
                return html
            except requests.exceptions.RequestException:
                logging.warning("retry " + url)
                i += 1
        return None

    # 请求主页
    def _request_index(self) -> str:
        return self._get(self._book_info.url, "请求主页失败")
    
    # 请求章节
    def _request_chapter(self, chapter: Chapter):
        return self._get(chapter.url, "请求章节失败")

    # 获取书籍信息
    def getBookInfo(self) -> BookInfo:
        return self._book_info

    # 获取章节列表
    def getChapterList(self) -> list[Chapter]:
        return self._chapters

    def save(self, path: str = None):
        if path is None: path = self._book_info.title + '.txt'
        with open(path, 'w', encoding='utf-8') as f:
            for chapter in self._chapters:
                f.write(chapter.title + '\n')
                f.write(chapter.getContent() + '\n')
                f.write('\n')
        logging.info("保存成功：" + path)

    # 解析主页
    def _parse_index(self, index_data):
        pass

    # 初始化所有章节内容
    def initChapters(self):
        pass

    # 初始化|解析 指定章节内容
    def initChapter(self, chapter: Chapter):
        pass


    # 设置线程池大小
    def setThreaPoolWorkers(self, workers: int):
        self._thread_pool_workers = workers
