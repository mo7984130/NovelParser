import logging

import requests
from NovelParser import NovelParser
from ProxyManager import ProxyManager, HttpProxy

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

def getNewProxy():
    data = requests.get("https://sch.shanchendaili.com/api.html?action=get_ip&key=HUd31cc9618108694175C1Lu&time=10&count=1&type=text&textSep=1&province=1886&city=1887&only=0").text.replace('\n', '')
    proxy = HttpProxy(data.split(':')[0], data.split(':')[1])
    proxy.setLifeTime(10 * 60)
    proxy.setMaxUseCount(100)
    return proxy

if __name__ == "__main__":
    proxyManager = ProxyManager(4, getNewProxy)
    parser = NovelParser.getParser("http://www.xsbiquge.la/book/34292/")
    proxyManager.init()
    parser.setProxyManager(proxyManager)
    parser.init()
    logging.info(parser.getBookInfo())
    parser.setThreaPoolWorkers(400)
    parser.initChapters()
    parser.save()