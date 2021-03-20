import argparse
import json
import os
import subprocess
from subprocess import SubprocessError
import urllib.parse
import datetime
import traceback
import shutil

TIME_DLIM = '~'  # 时间轴信息切割符号
VIDEO_DIR = 'videos'  # 视频输出文件夹
AUDIO_DIR = 'audios'  # 默认音频输出文件夹
TARGET = 'target'  # 目标视频文件名
MIN_DURATION = 1  # 音频最小持续时间（秒）
# 时间戳格式
TIMESTAMP_FORMATS = {
    "%H:%M:%S",  # HH:MM:SS
    "%H:%M:%S.%f",  # HH:MM:SS.mm
    "%M:%S",  # MM:SS
    "%M:%S.%f"  # MM:SS.mm
}
# 需科学上网的网站，可跳过
SKIPS = {
    'youtube'
}

# 创建文件夹
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

# 拆分时间轴信息，返还表示开始和结束时间的字符串（HH:MM:SS.mm）
def duration(expression):
    start, end = expression.split(TIME_DLIM)
    start = timestamp(start)
    end = timestamp(end)
    if start and end:
        if start >= end:  # 确保最小持续时间
            end = start + datetime.timedelta(seconds=MIN_DURATION)
        return start.strftime('%H:%M:%S.%f'), end.strftime('%H:%M:%S.%f')
    return None, None

# 将表示时间戳的字符串转化为datetime对象
def timestamp(expression):
    for form in TIMESTAMP_FORMATS:  # 尝试各种格式
        try:
            return datetime.datetime.strptime(expression, form)
        except ValueError:
            pass
    return None, None

# 根据url下载并保存视频至{dst}/{TARGET}.{ext}，返还本地视频位置
def download(url, dst):
    try:
        subprocess.run([
            'you-get',  # 下载器
            url,  # 视频链接
            '-o', dst,  # 输出文件夹
            '-O', TARGET,  # 输出文件名，不包含文件格式
        ])
        # 搜索本地视频位置
        for item in os.listdir(dst):
            path = os.path.join(dst, item)
            if os.path.isfile(path):
                name, ext = os.path.splitext(item)
                if name == TARGET:
                    return path

    except SubprocessError:
        traceback.print_exc()
    return None

# 根据start和end时间戳截取src视频片段并输出音频至dst，默认不覆盖已存在文件；
# 成功则返还True，否则返还False
def cut(src, dst, start, end, force=False):
    try:
        subprocess.run([
            'ffmpeg',  # 视/音频处理器
            '-y' if force else '-n',  # 默认"-n"不覆盖已存在文件，"-y"覆盖
            '-ss', start,  # 开始时间
            '-to', end,  # 结束时间
            '-i', src,  # 输入视频文件
            '-vn',  # 不读取视频信息
            '-af', 'loudnorm',  # 响度均衡
            '-ac', '2',  # 双声道
            dst,  # 输出音频文件
        ])
        return True
    except SubprocessError:
        traceback.print_exc()
    return False

# 从url中提取网站，视频号和分p信息
def video_id(url):
    components = urllib.parse.urlparse(url)
    for website in WEBSITES:
        netlocs = WEBSITES[website]['netlocs']
        if components.netloc in netlocs:
            token, part = netlocs[components.netloc](components)
            # 检验视频号是否符合标准
            if len(token) == WEBSITES[website]['length']:
                return website, token, part
    return None, None, None

# 提取Bilibili链接中的视频号和分p号
# 链接格式：https://www.bilibili.com/video/<视频号>
#          https://www.bilibili.com/video/<视频号>?p=<分p号>
def bilibili_id(components):
    token = components.path.rsplit('/', 1)[-1]  # 提取视频号
    part = urllib.parse.parse_qs(components.query)  # 提取分p号
    if 'p' in part:
        return token, part['p'][0]
    return token, None

# 提取YouTube链接中的视频号，不提取分p号（播放列表中的视频链接包含原视频号）
# 链接格式：https://www.youtube.com/watch?v=<视频号>
#          https://www.youtube.com/watch?v=<视频号>&ab_channel=<频道名>
#          https://www.youtube.com/watch?v=<视频号>&list=<播放列表号>&index=<分p号>
def youtube_id(components):
    return urllib.parse.parse_qs(components.query)['v'][0], None

# 支持网站信息
# {
#   网站1名称: {
#       域名格式: {
#           域名格式1: 提取视频号和分p号的函数,
#           域名格式2: ...
#       },
#       视频号标准长度
#   },
#   网站2名称: ...
# }
WEBSITES = {
    'bilibili': {
        'netlocs': {
            'www.bilibili.com': bilibili_id,
        },
        'length': 12,  # 包括BV
    },
    'youtube': {
        'netlocs': {
            'www.youtube.com': youtube_id,
        },
        'length': 11,
    },
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='下载视频并截取音频')
    parser.add_argument('-i', '--input', type=str, help='视频列表文件 (.json)')
    parser.add_argument('-o', '--output', type=str, default=AUDIO_DIR, help='音频输出地址')
    parser.add_argument('-e', '--encoding', type=str, default='utf-8', help='视频列表文件编码')
    parser.add_argument('-f', '--force', action='store_true', help='覆盖已存在音频')
    parser.add_argument('-d', '--delete', action='store_true', help='完成时删除视频')
    parser.add_argument('-s', '--skip', action='store_true', help='跳过需科学上网的网站')
    options = parser.parse_args()

    # 读取视频列表文件并创建视/音频输出文件夹
    with open(options.input, 'r', encoding=options.encoding) as f:
        metadata = json.load(f)
    create_directory(options.output)
    create_directory(VIDEO_DIR)

    success = 0
    skip = 0
    for i, info in enumerate(metadata):
        print(f"正在处理 ({i + 1}/{len(metadata)}): {info['name']}")
        url = info['mark']['url']
        website, token, part = video_id(url)  # 提取网站名，视频号和分p号

        if website and token:
            # 根据选项跳过需科学上网的网站
            if options.skip and website in SKIPS:
                skip += 1
                print('跳过')
            else:
                # 按照网站名创建第二级视频输出文件夹
                website_dir = os.path.join(VIDEO_DIR, website)
                create_directory(website_dir)
                # 按照视频号创建第三级视频输出文件夹
                save_dir = os.path.join(website_dir, token)
                create_directory(save_dir)
                if part:  # 如有分p号，按照分p号创建第四级视频输出文件夹
                    save_dir = os.path.join(save_dir, part)
                src = download(url, save_dir)  # 下载并获取本地视频位置
                
                start, end = duration(info['mark']['time'])  # 获取开始和结束时间
                if start and end:
                    dst = os.path.join(options.output, info['path'])  # 输出音频文件的位置
                    if cut(src, dst, start, end, force=options.force):
                        success += 1
        print()
    print(f'成功 ({success}/{len(metadata)}), 跳过 {skip}, 失败 {len(metadata) - success - skip}')

    if options.delete: # 根据选项删除视频输出文件夹
        shutil.rmtree(VIDEO_DIR)
        print('成功移除视频文件夹')
