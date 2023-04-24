# 真白萌爬虫
Masiro-Spider的部分功能仍在开发阶段...

许多地方参考了这个项目：https://github.com/ilusrdbb/lightnovel-pydownloader
他的缺点是只能爬取真白萌排行榜，而不能爬取用户收藏。我的程序正好相反。

## 功能
模拟登录，将用户收藏的小说下载到本地。
- 采用异步操作，效率较高；
- 文本与插图都可下载，封面图片与评论图片暂不支持下载；
- 需要在文档中填写文件保存路径、用户名、登录密码、爬取的页面范围等参数；
- 并发规模、连接失败的重试次数、延迟请求时间、单个任务下载超时时间等参数可调；
- 暂不支持付费章节的购买与下载；
- 暂不支持自动点赞。

## 环境
- python 3.6 ~ 3.10 (使用了3.11中被取消的方法)
- 安装aiohttp, aiofiles, lxml, 以及脚本运行时提示依赖的库

## 参考
- 通用轻小说网站爬虫工具 https://github.com/ilusrdbb/lightnovel-pydownloader
- 异步http请求aiohttp模块讲解 BV1YM411s72j BV1sT411a76H
- 异步爬虫实战 BV1W54y1M7un BV1ax4y1T77x
- Xpath语法 BV1j7411d7s9
