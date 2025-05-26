__LAST_MODIFY__: str = "2025/05/12"

from bs4 import BeautifulSoup
import logging

import sys
sys.path.append('../')
from NovelParser import Chapter, NovelParser

__all__ = ['Parser']

# 新笔趣阁网站解析器
class Parser(NovelParser):
    _base_host_url = "http://www.xsbiquge.la"

    # 请求并解析主页
    def _parse_index(self, index_data):
        # 请求主页
        soup = BeautifulSoup(index_data, 'html.parser')
        # 获取书籍信息
        self._parse_book_info_div(soup.find('div', attrs={'id':'info'}))
        # 解析章节信息
        self._parse_chapter_list_div(soup.find('div', attrs={'class':'listmain'}))

    # 解析书籍信息
    def _parse_book_info_div(self, book_info_div):
        self._book_info.title = book_info_div.find('h1').text
        self._book_info.author = book_info_div.find('p').text

    # 解析章节信息
    def _parse_chapter_list_div(self, chapter_list_div):
        chapter_list_dl = chapter_list_div.find('dl')
        dds = chapter_list_dl.find_all('dd')
        dds = dds[5:]
        self._chapters = []
        for dd in dds:
            self._last_no += 1
            a = dd.find('a')
            cpt = Chapter()
            cpt.title = a.text.replace(' ', '')
            cpt.url = self._base_host_url + a.get('href')
            cpt.no = self._last_no
            self._chapters.append(cpt)

    # 初始化指定章节内容
    def initChapter(self, chapter: Chapter):
        contents = BeautifulSoup(self._request_chapter(chapter), 'html.parser').find_all('p', attrs={'class':'content_detail'})
        chapter.content = ''
        for content in contents:
            chapter.content += "    " + content.text.strip() + '\n'
        logging.info(str(chapter) + "爬取完毕")