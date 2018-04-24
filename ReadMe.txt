2018 - 01 - 14
在原基础上加入在通过手机验证码操作，用的是LeanCloud

首页：
静态页面

文件传输：
限制文件大小，在本地使用app.run()上传会阻塞，因为Flask自带的http server Werkzurg 性能较差，默认使用单进程单线程

告白墙：
是静态页面

写文章：
原发布文章用flask db.model form写的，现改成使用TinyMCE文章编辑器，发布之后因为不会把内容渲染到TinyMCE的编辑框内，所以返回来重新编辑文章时不能再使用TinyMCE编辑，继续使用flask的form编辑文章，又因为用TinyMCE编辑器发布文章时含有html标签在数据库里，所以重新编辑文章时要先去掉html标签只留下文字（图片在img标签里，重新编辑就没图片了，这是个bug），然后传到form里。

文章详情页：
window.onload = Ajax异步加载文章内容

文章评论：
触发js事件，Ajax异步加载

实时翻译：
破解有道翻译API,判断用户是否完成输入（1s不按键代表输入结束），完成输入发送请求，用ajax异步把翻译结果加载到页面上。


REST WEB API开发：
1，用户
http://127.0.0.1:5000/api/v1.0/users/1                                  # 用户1信息
http://127.0.0.1:5000/api/v1.0/users/1/posts/                           # 用户1发布的所有文章
http://127.0.0.1:5000/api/v1.0/users/1/posts/?page=2                    # 用户1发布的所有文章第二页..
http://127.0.0.1:5000/api/v1.0/posts/1/comments/                        # 用户1发布的所有评论
http://127.0.0.1:5000/api/v1.0/posts/1/comments/?page=2                 # 用户1发布的所有评论第二页..
http://127.0.0.1:5000/api/v1.0/users/1/confessions/                     # 用户1所有告白内容
http://127.0.0.1:5000/api/v1.0/users/1/confessions/?page=2              # 用户1所有告白内容第二页..
http://127.0.0.1:5000/api/v1.0/users/1/followed_articles/               # 用户1关注的所有文章
http://127.0.0.1:5000/api/v1.0/users/1/followed_articles/?page=2        # 用户1关注的所有文章第二页..

2，文章
http://127.0.0.1:5000/api/v1.0/posts/                                   # 网站所有文章
http://127.0.0.1:5000/api/v1.0/posts/?page=2                            # 网站所有文章第二页..
http://127.0.0.1:5000/api/v1.0/posts/7                                  # id=7的文章
http://127.0.0.1:5000/api/v1.0/posts/7/comments/                        # id=7文章下的评论
http://127.0.0.1:5000/api/v1.0/posts/7/comments/?page=2                 # id=7文章下的评论第二页..

3，评论
http://127.0.0.1:5000/api/v1.0/comments/                                # 网站所有评论
http://127.0.0.1:5000/api/v1.0/comments/?page=2                         # 网站所有评论第二页..
http://127.0.0.1:5000/api/v1.0/comments/1                               # id=1的评论

4，告白
http://127.0.0.1:5000/api/v1.0/confessions/                             # 网站所有告白
http://127.0.0.1:5000/api/v1.0/confessions/?page=2                      # 网站所有告白第二页..
http://127.0.0.1:5000/api/v1.0/confessions/2                            # id=2的告白
