# 使用说明

---

## 简介

- 该项目可根据输入的`.json`文件完成以下步骤
  - 下载网络视频
  - 截取视频片段
  - 输出截取后的`.mp3`音频

## 所需程序

- [Python3 (需包含pip)](https://www.python.org/downloads/)
- 视/音频处理器：[FFmpeg](https://ffmpeg.org/download.html)
- 视频下载器：[You-Get](https://github.com/soimort/you-get)

## 运行方式

```bash
usage: run.py [-h] [-i INPUT] [-o OUTPUT] [-e ENCODING] [-f] [-d] [-s]

下载视频并截取音频

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        视频列表文件 (.json)
  -o OUTPUT, --output OUTPUT
                        音频输出地址
  -e ENCODING, --encoding ENCODING
                        视频列表文件编码
  -f, --force           覆盖已存在音频
  -d, --delete          完成时删除视频
  -s, --skip            跳过需科学上网的网站
```

- 举例
  - 常规下载并截取音频

    ```bash
    python run.py -i path/to/input.json -o path/to/output_directory
    ```

  - 覆盖输出文件夹内同名音频（视频不会）

    ```bash
    python run.py -i path/to/input.json -o path/to/output_directory -f
    ```

  - 跳过YouTube视频

    ```bash
    python run.py -i path/to/input.json -o path/to/output_directory -s
    ```

## 输入内容结构

- 包含至少以下内容

```json
[
  {
    "name": "<音频介绍>",
    "path": "<音频文件名>",
    "mark": {
      "time": "<开始时间>~<结束时间>",
      "url": "<视频链接>"
    }
  }
]
```

- 音频文件名需包含文件格式
- 开始时间和结束时间可选格式：
  - `HH:MM:SS`
  - `HH:MM:SS.mm`
  - `MM:SS`
  - `MM:SS.mm`

## 视频文件夹结构

- 第一级：`videos`
- 第二级：按照视频网站名称
- 第三级：按照视频号
- 第四级（如果有）：按照分p号
- 举例：

    ```text
    videos
    |---bilibili
    |   |---BV15h41117Hx
    |   |   \---target.mp4
    |   \---BV1WE411777P
    |       \---1
    |           \---target.mp4
    \---youtube
        \---g9vi0AlraZI
            \---target.mp4
    ```

## 支持的视频网站及默认链接范例

- `Bilibili`
  - 常规：`https://www.bilibili.com/video/<视频号>`
  - 分p：`https://www.bilibili.com/video/<视频号>?p=<分p号>`
- `YouTube`
  - 常规：`https://www.youtube.com/watch?v=<视频号>`
  - 分p：`https://www.youtube.com/watch?v=<视频号>&list=<播放列表号>&index=<分p号>`

## 注意事项

- `You-Get`若报错可能需要更新

  ```bash
  pip install -U you-get
  ```

- 音频最小截取长度默认为`1`秒

---
