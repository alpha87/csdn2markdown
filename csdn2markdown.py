#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 - Time: 2019-06-26 08:20
 - Author: Jianxun
 - Site: https://lijianxun.top
 - File: csdn2markdown.py
 - Software: PyCharm
 - Description:
   - CSDN 文章转 Markdown
"""

import re
import requests
import execjs
import html2text
from bs4 import BeautifulSoup


class CSDN2Markdown(object):

    def __init__(self, user_url, hexo=False):
        self.hexo = hexo
        self.user_url = user_url
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/75.0.3770.100 Safari/537.36"
        }

    def spider(self, url):
        """
            封装请求

            直接返回 BeautifulSoup 对象
        """

        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return BeautifulSoup(response.text, "lxml")

    def get_all_articles_url(self, blog_url: str) -> list:
        """
            获取用户所有文章的 URL

            参数：

                - blog_url: 需要下载的博客链接，例如：https://blog.csdn.net/A_lPha

            返回：

                - 文章列表
        """

        soup = self.spider(blog_url)
        all_script = soup.find_all("script")
        pages_script = None
        for script in all_script:
            if "listTotal" in str(script):
                pages_script = str(script)
        page_size = re.findall('var pageSize = (\d+) ;', pages_script)[0]
        list_total = re.findall('var listTotal = (\d+) ;', pages_script)[0]
        page_total = round(int(list_total)/int(page_size))
        pages_script = pages_script.replace(
            "<script>", "").replace("</script>", "")
        ctx = execjs.compile(pages_script)
        return [ctx.call("getAllUrl", page)
                for page in range(1, page_total+1)]

    def get_all_articles(self, url_list: list) -> list:
        """
            通过文章列表的 URL 获取用户所有文章

            参数：

                - url_list: 所有文章列表的链接

            返回：

                - 每则博文的 URL
        """

        all_titles = list()
        for url in url_list:
            soup = self.spider(url)
            titles = soup.find_all("h4", class_="")
            all_titles.extend(
                [title for title in titles
                 if "article-type type-1 float-none" in str(title)]
            )
        return [re.findall('a href="(.*?)" target', str(item))[0]
                for item in all_titles]

    def html2markdown(self, url: str):
        """
            将 URL 获取到的 html 文本转化为 markdown

            参数：

                - url: 文章列表

            返回：

                - markdown 格式的文本
        """

        soup = self.spider(url)
        title = soup.find("h1", class_="title-article").string
        date = str(soup.find("span", class_="time").string).replace("年", "-").replace("月", "-").replace("日", "")
        article = soup.find("div", class_="markdown_views")
        article.svg.extract()
        text = str(article)
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.code = True
        doc = h.handle(text)

        self.writer(title, date, doc)

    def writer(self, title: str, date: str, doc: str):
        """
            将转换完成的 markdown 保存到文件中

            参数：

                - title: 文章标题
                - doc: 文章正文
        """
        if self.hexo:
            head = """
            ---
            title: {title}
            copyright: true
            date: {date}
            categories: 零基础学 Python
            tags:
             - python
             - 学习
             - 编程
            ---
            """.format(title=title, date=date)
            with open("{}.md".format(title), "w") as f:
                f.write(head)
                f.write(doc)
                print("{} [ 完成 ]".format(title))
        else:
            with open("{}.md".format(title), "w") as f:
                f.write(doc)
            print("{} [ 完成 ]".format(title))

    def run(self):
        """
            跑起来就完事了
        """

        all_url_list = self.get_all_articles_url(self.user_url)
        articles = self.get_all_articles(all_url_list)
        for url in articles:
            self.html2markdown(url)


if __name__ == '__main__':
    s = CSDN2Markdown("https://blog.csdn.net/A_lPha", hexo=True)
    s.run()
