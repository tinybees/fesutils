## fesutils Changelog

###[1.0.0b3] - 2020-9-3

#### Changed
- 修改部分类型标注
- 修改schema校验适配最新的sanic框架上下文传值方式


###[1.0.0b2] - 2020-3-20

#### Changed
- 升级marshmallow的最低版本为3.0.0
- 由于marshmallow版本升级,更改schema校验功能
- 去掉工具类打印日志的功能
- 修改生成随机值位数不够的问题
- 修复定时任务工具类中会造成多个worker都加载定时任务的问题

###[1.0.0b1] - 2020-3-2

#### Added
- 增加cacheutils库,包含LRI,LRU,Singleton, Cached,g等等
- 增加objectid库,可以直接生成objectid
- 增加线程池的pool,pool_submit库等
- 增加string相关的多个方法
- 增加调度相关的方法
- 增加解析相关的库方法,包含yaml等
- 增加包装相关的库,包括单个方法的包装和多个方法的包装
- 增加schema校验相关的方法适用于flask以及sanic,以及生成swagger方法
- schema中增加根据schema生成其他schema的功能,用于分表,分库同表等的用途
- schema中增加更改marshmallow中fields中各个类型的默认错误消息的功能
- 增加同步异步执行命令的工具类
- 增加时间解析和格式化的工具类,包括gmt,iso,ymd,timestamp等
