# nowcoder-board-overview
A simple server to monitor nowcoder board status.

一个较为简单的 Flask 小程序，用于将牛客的 ACM 榜单信息转换为类 DOMJudge 格式的榜单信息。
可用作多校赛 / 校内训练赛 / 复现赛期间的大屏幕榜单展示。

赶鸭子上架型的项目，代码写得比较烂，如果有人能来完善的话就太好了。

## 使用方法

启动 Flask 项目后， `http://127.0.0.1:5000/?contestId=牛客竞赛 ID` 即可查看榜单。
更多功能通过追加参数完成：
- scroll: 滚动榜单时间
- refresh: 刷新榜单时间，**仅在设置了 `scroll` 时有效**
- searchName：在牛客的搜索关键词，可用于过滤学校。

## 鸣谢

没有以下项目，本项目将无法完成：

- [XCPCIO](https://github.com/xcpcio/board-spider/blob/8a1b08372e7b8d3db1cf41d74784d786327b3377/xcpcio_board_spider/spider/nowcoder/v1/nowcoder.py) 项目，提供了基础的数据类型架构和牛客的初版爬虫代码，本项目在此基础上进行了修改和扩展，修改了致命 BUG 并添加了更多爬虫 。
- [SUA.AC](https://sua.ac/wiki/2023-icpc-jinan/board/) 项目，提供了基础的前端代码与前端计算逻辑。
- [牛客网](https://ac.nowcoder.com/) 的数据支持。