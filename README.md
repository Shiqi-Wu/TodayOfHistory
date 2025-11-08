# TodayOfHistory

这是 `TodayOfHistory` 的说明与使用文档。该脚本会把存放在指定目录内、按时间戳和文案命名的文件夹中的视频或图片，自动发布为微博（支持视频单发和多图图文）。该仓库可以用于半自动化发布粉丝社群或其他运营“那年今日”栏目。

## 文件说明
- `auto_post_weibo_selenium.py`：自动发布脚本（已改为读取 `config.json`）。
- `config.json`：配置信息（见下文）。

## 配置 (`config.json`)
示例（已包含在仓库）:

```json
{
  "base_dir": "/Users/shiqi/Documents/Personal-Code-Tools/douyin-downloader/Downloaded/孙亦航.",
  "template": "#孙亦航[超话]#\n\n那年今日（{year}{month}{day}）dy更新\n\n“{hashtags}”\n\n@孙亦航mew ",
  "login_wait": 30,
  "upload_wait": 25,
  "chrome_detach": true,
  "browser_maximize": true,
  "image_extensions": [".jpg", ".jpeg", ".png", ".gif"],
  "video_extensions": [".mp4", ".mov"]
}
```

字段说明：
- `base_dir`：要扫描的父目录，脚本会遍历该目录下的子文件夹（见命名规范）。
- `template`：微博正文模板，支持占位符 `{year}`、`{month}`、`{day}`、`{hashtags}`。
- `login_wait`：打开微博页面后等待用户手动登录的秒数（默认 30s）。
- `upload_wait`：上传文件后等待的秒数（默认 25s）。
- `chrome_detach`：是否让 Chrome 在脚本结束后保持打开（true/false）。
- `browser_maximize`：是否尝试最大化浏览器窗口。
- `image_extensions` / `video_extensions`：识别图片/视频文件的扩展名。

## 文件夹命名规范
脚本假设 `base_dir` 下有以时间戳开头并包含文案的子文件夹，格式类似：

```
2019-07-06_17-19-12_再也不敢坐儿童车了！  修完赶紧溜了！！！😱ི/
```

本项目中，使用的是 https://github.com/jiji262/douyin-downloader 中的抖音下载工具。

格式说明：
- 前缀为 `YYYY-MM-DD_HH-MM-SS_`，后面紧跟一段描述/文案（脚本会把时间戳后的那部分作为 `hashtags` 或文案的来源）。
- 子文件夹内放入对应的媒体文件：
  - 视频文件（比如 `.mp4`、`.mov`）——每个视频将作为单独一条微博发布。
  - 图片文件（比如 `.jpg`、`.png`）——如果文件夹中有多张图片，脚本会把该文件夹中的所有图片作为一条多图微博一次性上传（图文）。

例：
```
Downloaded/孙亦航./2019-07-06_17-19-12_再也不敢坐儿童车了！  修完赶紧溜了！！！😱ི/
  - clip1.mp4
  - thumb.jpg
  - extra1.jpg
  - extra2.png
```
上述示例会生成：
- 一条视频帖（`clip1.mp4`）
- 一条图文帖（`thumb.jpg`, `extra1.jpg`, `extra2.png`，多图一次上传）

## 运行逻辑（高层说明）
1. 脚本读取 `config.json`（可通过命令行参数 `--config` 指定其他路径）。
2. 遍历 `base_dir` 下的子目录，使用正则 `^(YYYY)-(MM)-(DD)_` 匹配日期前缀。
3. 找到与今天（脚本运行当天）的月-日相同的文件夹（`MM-DD`），提取年份/月份/日子并把文件夹名中时间戳后面的文本作为 `hashtags` 文案的一部分。
4. 在该文件夹中：
   - 把识别为视频的文件（按 `video_extensions`）逐个作为单条视频微博加入任务队列。
   - 把识别为图片的文件（按 `image_extensions`）全部收集到同一条多图微博任务中（如果存在图片）。
5. 启动 Chrome（通过 webdriver-manager 自动安装 chromedriver），打开 `weibo.com` 并等待 `login_wait` 秒以便手动登录（或已登录会直接继续）。
6. 对每个待发送任务：
   - 打开微博首页，点击发文输入框并填入根据 `template` 生成的文本。
   - 如果任务包含文件，找到 `input[type=file]` 并上传：
     - 视频：单个文件上传。
     - 多图：把多张图片的绝对路径以换行符连接传给 `send_keys`，以便一次性上传多个文件（文件输入支持 multiple）。
7. 所有任务完成后浏览器保持打开（若 `chrome_detach` 为 true），脚本会等待用户按 Enter 退出。（在当前版本下，不能够自动发布，需要用户审核后自己点击发送键）

## 使用方式
在 `TodayOfHistory` 目录下：

```bash
# 使用仓库内的默认 config.json
python auto_post_weibo_selenium.py

# 或指定其他配置文件路径
python auto_post_weibo_selenium.py --config /path/to/your/config.json
```

提示：
- 脚本使用 `webdriver-manager` 来管理 chromedriver。确保 Python 环境已安装 `selenium` 和 `webdriver-manager`。
- 如果上传等待时间不够，请在 `config.json` 中适当调大 `upload_wait`。

## 依赖
请在你的 Python 环境中安装：

```
pip install selenium webdriver-manager
```


## 注意事项与限制
- 脚本基于页面元素和文字（如“有什么新鲜事”输入框），如果微博页面结构或语言发生变化，可能需要调整选择器或 XPATH。
- 上传多图依赖页面的文件 input 支持 multiple 属性（微博通常支持）。
- 发布按钮的识别为启发式实现；如果仍无法自动点击，请手动点击一次发布以完成任务。