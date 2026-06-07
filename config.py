"""全局配置"""

from pathlib import Path

# 默认输出目录
DEFAULT_OUTPUT_DIR = Path("E:/Obsidian/主仓库/11-subtitles")

# 请求相关
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# 并发控制
DEFAULT_MAX_WORKERS = 3
DEFAULT_DELAY_BETWEEN_REQUESTS = (1.0, 2.5)

# Bilibili API
BILI_VIEW_API = "https://api.bilibili.com/x/web-interface/view"
BILI_PLAYER_WBI_API = "https://api.bilibili.com/x/player/wbi/v2"
BILI_PLAYER_V2_API = "https://api.bilibili.com/x/player/v2"
BILI_SERIES_API = "https://api.bilibili.com/x/series/archives"
BILI_COLLECTION_API = "https://api.bilibili.com/x/series/archives"
BILI_FAVLIST_API = "https://api.bilibili.com/x/v3/fav/resource/list"

# 文件名安全映射
FILENAME_BAD_CHARS = '\\/:*?"<>|'
FILENAME_MAX_LENGTH = 80

# 字幕语言优先级（数值越小越优先）
SUBTITLE_LANG_PRIORITY = {
    "zh-cn": 0,
    "zh-hans": 0,
    "zh": 1,
    "ai-zh": 2,
    "ai-zh-cn": 2,
    "en": 10,
    "en-us": 10,
    "en-gb": 10,
    "ai-en": 11,
}

# 默认请求头
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.0 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0"
    ),
    "Referer": "https://www.bilibili.com",
}
