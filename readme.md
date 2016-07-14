### huihui clawer

	Python3.x+
	MongoDB

用来抓取[慧慧网：逛折扣频道](http://www.huihui.cn/hotdeal)下实时发布的物品，并且通过邮件发送出来。

####整体思路：
1.  直接访问那个页面发现并不能在HTML里看到物品信息，发现这个网站会在加载完毕后通过JavaScript向服务器的API接口请求物品信息并展现出来，所以通过浏览器的开发者工具找到[API接口](http://www.huihui.cn/recommenddeal/data.json?domain=all&page=1&maxId=0&pagebar=1&sort=0&_=1468421029126)，就可以直接访问得到JSON数据。
2. 不需要用BeautifulSoup，他们的JSON数据十分工整，直接遍历items，不在数据库中的，添加到数据库，并且添加到items_to_email[]
3. 调用send_email()将items_to_mail[]发送出去
4.  将上述过程每60秒钟执行一次(慧慧网这个频道的更新频率非常低)（为保证http请求和发送邮件时不被阻塞，需要做异步。本想用Python3.4标准库的[asyncio](https://docs.python.org/3.5/library/asyncio.html)来做异步，结果看了半天还是不会用，所以暂时先用了Threading这个路子）


代码结构和功能的封装可能做的不太合理，请见谅。我会多看看开源项目学习学习。

（请先配置config.py里的内容）