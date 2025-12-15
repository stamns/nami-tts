import urllib.request
import urllib.parse
import hashlib
import json
import os
import logging
import gzip
import ssl
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import random
import time
import io
import concurrent.futures

from backend.utils.audio import validate_and_normalize_mp3

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None


class NanoAITTS:
    def __init__(self):
        self.name = '纳米AI'
        self.id = 'bot.n.cn'
        self.author = 'TTS Server'
        self.icon_url = 'https://bot.n.cn/favicon.ico'
        self.version = 2
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        self.voices = {}
        self.logger = logging.getLogger('NanoAITTS')  # 添加专用日志器
        
        # 加载配置
        self.cache_dir = os.getenv('CACHE_DIR', '/tmp/cache')
        self.http_timeout = int(os.getenv('HTTP_TIMEOUT', '30'))
        self.retry_count = int(os.getenv('RETRY_COUNT', '2'))
        
        # 处理代理配置，增强验证逻辑
        raw_proxy_url = os.getenv('PROXY_URL', '').strip()
        self.proxy_url = self._validate_and_clean_proxy_url(raw_proxy_url)
        self.ssl_verify = os.getenv('SSL_VERIFY', 'true').lower() in ('true', '1', 'yes', 'on')
        
        self.logger.info(
            f"TTS引擎配置: timeout={self.http_timeout}s, retry={self.retry_count}, proxy_enabled={bool(self.proxy_url)}, ssl_verify={self.ssl_verify}"
        )
        if self.proxy_url:
            self.logger.info(f"代理配置: {self.proxy_url}")
        else:
            self.logger.info("代理配置: 未启用 (使用直连)")

        # 时间同步/偏差诊断（用于修复Vercel容器时间漂移导致的110023）
        self.time_sync_enabled = os.getenv('TIME_SYNC_ENABLED', 'true').lower() in ('true', '1', 'yes', 'on')
        self.time_drift_threshold_seconds = int(os.getenv('TIME_DRIFT_THRESHOLD_SECONDS', '30'))
        self.time_sync_interval_seconds = int(os.getenv('TIME_SYNC_INTERVAL_SECONDS', '300'))
        self.time_sync_url = os.getenv('TIME_SYNC_URL', 'https://bot.n.cn').strip() or 'https://bot.n.cn'
        self.time_sync_use_server_time_on_drift = (
            os.getenv('TIME_SYNC_USE_SERVER_TIME_ON_DRIFT', 'true').lower() in ('true', '1', 'yes', 'on')
        )

        self._time_offset_seconds: Optional[float] = None
        self._time_offset_checked_at: Optional[float] = None
        self._last_server_epoch_seconds: Optional[float] = None
        self._last_server_date_header: Optional[str] = None
        self._last_time_sync_error: Optional[str] = None
        self._last_request_time_info: Optional[Dict[str, Any]] = None

        self.logger.info(
            "时间同步配置: enabled=%s, drift_threshold=%ss, interval=%ss, url=%s, use_server_time_on_drift=%s",
            self.time_sync_enabled,
            self.time_drift_threshold_seconds,
            self.time_sync_interval_seconds,
            self.time_sync_url,
            self.time_sync_use_server_time_on_drift,
        )
        if self.time_sync_enabled:
            try:
                self.sync_time_offset(force=True)
            except Exception as e:
                self.logger.warning(f"启动时时间同步检查失败: {str(e)}")

        self._ensure_cache_dir()  # 确保缓存目录存在
        self.load_voices()
    
    def _validate_and_clean_proxy_url(self, raw_url: str) -> Optional[str]:
        """
        验证和清理代理URL
        移除无效字符，检查URL格式，返回有效的代理URL或None
        """
        if not raw_url:
            return None
        
        # 简单的字符串预处理
        url = raw_url.strip()
        
        # 如果为空，返回None
        if not url:
            return None
        
        # 移除注释内容（从第一个 # 开始）
        if '#' in url:
            url = url.split('#')[0].strip()
        
        # 移除控制字符
        url = ''.join(char for char in url if ord(char) >= 32 and char not in ['\t', '\n', '\r'])
        
        # 最终清理
        url = url.strip()
        
        # 如果为空，返回None
        if not url:
            return None
        
        # 验证基本格式
        if not url.startswith(('http://', 'https://')):
            if '://' in url:
                # 包含其他协议，不支持
                self.logger.error(f"不支持的代理URL协议: {url}")
                return None
            else:
                # 添加默认协议
                url = 'http://' + url
        
        # 使用 urllib.parse 进行验证
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # 检查基本组件
            if not parsed.scheme or not parsed.hostname:
                self.logger.error(f"无效的代理URL: {url}")
                return None
            
            # 检查端口
            if parsed.port is not None:
                if not isinstance(parsed.port, int) or not (1 <= parsed.port <= 65535):
                    self.logger.error(f"无效的代理端口: {parsed.port}")
                    return None
            
            # 重新构造清洁的URL
            result = f"{parsed.scheme}://{parsed.hostname}"
            if parsed.port:
                result += f":{parsed.port}"
            
            self.logger.debug(f"代理URL验证成功: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"代理URL验证失败: {url}, 错误: {str(e)}")
            return None
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir, exist_ok=True)
                self.logger.info(f"创建缓存目录: {self.cache_dir}")
        except OSError as e:
            self.logger.error(f"创建缓存目录失败: {str(e)} (path: {self.cache_dir}, errno: {e.errno})", exc_info=True)
            if e.errno == 30:
                self.logger.error("检测到文件系统只读错误，请确保使用可写目录（如 /tmp）")
        except Exception as e:
            self.logger.error(f"创建缓存目录失败 (未预期的错误): {str(e)}", exc_info=True)

    def _get_opener(self) -> urllib.request.OpenerDirector:
        handlers = []

        if self.proxy_url:
            handlers.append(
                urllib.request.ProxyHandler({'http': self.proxy_url, 'https': self.proxy_url})
            )

        if not self.ssl_verify:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            handlers.append(urllib.request.HTTPSHandler(context=ssl_context))

        return urllib.request.build_opener(*handlers)

    def _parse_http_date_to_epoch(self, date_header: str) -> Optional[float]:
        if not date_header:
            return None

        try:
            dt = parsedate_to_datetime(date_header)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            return None

    def sync_time_offset(self, force: bool = False) -> Dict[str, Any]:
        """从上游响应头Date获取服务器时间，计算本地时间偏差。

        说明：Vercel等Serverless容器可能存在系统时间漂移，导致签名校验失败（110023）。
        """

        status = {
            "enabled": self.time_sync_enabled,
            "sync_url": self.time_sync_url,
            "threshold_seconds": self.time_drift_threshold_seconds,
            "interval_seconds": self.time_sync_interval_seconds,
            "checked_at_epoch": self._time_offset_checked_at,
            "server_date_header": self._last_server_date_header,
            "server_epoch_seconds": self._last_server_epoch_seconds,
            "offset_seconds": self._time_offset_seconds,
            "local_epoch_seconds": time.time(),
            "error": self._last_time_sync_error,
        }

        if not self.time_sync_enabled:
            return status

        now = time.time()
        if (
            not force
            and self._time_offset_checked_at is not None
            and now - self._time_offset_checked_at < self.time_sync_interval_seconds
        ):
            return status

        opener = self._get_opener()
        headers = {"User-Agent": self.ua}

        # HEAD更轻量，但部分站点可能不支持
        request_methods = ["HEAD", "GET"]
        last_error: Optional[str] = None
        for method in request_methods:
            start = time.time()
            try:
                req = urllib.request.Request(self.time_sync_url, headers=headers, method=method)
                with opener.open(req, timeout=self.http_timeout) as response:
                    end = time.time()
                    date_header = response.headers.get('Date') or response.headers.get('date')
                    server_epoch = self._parse_http_date_to_epoch(date_header)

                    if server_epoch is None:
                        last_error = f"无法解析Date头: {date_header}"
                        continue

                    local_midpoint = (start + end) / 2
                    offset = server_epoch - local_midpoint

                    self._time_offset_seconds = offset
                    self._time_offset_checked_at = end
                    self._last_server_epoch_seconds = server_epoch
                    self._last_server_date_header = date_header
                    self._last_time_sync_error = None
                    last_error = None

                    drift = abs(offset)
                    self.logger.info(
                        "时间同步检查: server_epoch=%.3f local_epoch=%.3f offset=%.3fs drift=%.3fs method=%s",
                        server_epoch,
                        local_midpoint,
                        offset,
                        drift,
                        method,
                    )
                    if drift > self.time_drift_threshold_seconds:
                        self.logger.warning(
                            "检测到设备时间偏差过大(> %ss): offset=%.3fs。将尝试使用服务器时间生成timestamp以避免110023",
                            self.time_drift_threshold_seconds,
                            offset,
                        )

                    break

            except Exception as e:
                last_error = f"{method}请求失败: {str(e)}"

        if last_error:
            self._last_time_sync_error = last_error
            self.logger.warning(f"时间同步检查失败: {last_error}")

        return self.get_time_sync_status()

    def get_time_sync_status(self) -> Dict[str, Any]:
        now = time.time()
        drift = abs(self._time_offset_seconds) if self._time_offset_seconds is not None else None

        return {
            "enabled": self.time_sync_enabled,
            "sync_url": self.time_sync_url,
            "use_server_time_on_drift": self.time_sync_use_server_time_on_drift,
            "threshold_seconds": self.time_drift_threshold_seconds,
            "interval_seconds": self.time_sync_interval_seconds,
            "checked_at_epoch": self._time_offset_checked_at,
            "local_epoch_seconds": now,
            "server_date_header": self._last_server_date_header,
            "server_epoch_seconds": self._last_server_epoch_seconds,
            "offset_seconds": self._time_offset_seconds,
            "drift_seconds": drift,
            "error": self._last_time_sync_error,
        }

    def get_last_request_time_info(self) -> Optional[Dict[str, Any]]:
        return self._last_request_time_info

    def _get_effective_epoch_seconds(self) -> float:
        local_now = time.time()
        if (
            self.time_sync_enabled
            and self.time_sync_use_server_time_on_drift
            and self._time_offset_seconds is not None
            and abs(self._time_offset_seconds) > self.time_drift_threshold_seconds
        ):
            return local_now + self._time_offset_seconds

        return local_now

    def md5(self, msg):
        """MD5 哈希函数"""
        return hashlib.md5(msg.encode('utf-8')).hexdigest()
    
    def _e(self, nt):
        """生成哈希值"""
        HASH_MASK_1 = 268435455
        HASH_MASK_2 = 266338304
        
        at = 0
        for i in range(len(nt) - 1, -1, -1):
            st = ord(nt[i])
            at = ((at << 6) & HASH_MASK_1) + st + (st << 14)
            it = at & HASH_MASK_2
            if it != 0:
                at = at ^ (it >> 21)
        return at
    
    def generate_unique_hash(self):
        """生成唯一哈希"""
        lang = 'zh-CN'
        app_name = "chrome"
        ver = 1.0
        platform = "Win32"
        width = 1920
        height = 1080
        color_depth = 24
        referrer = "https://bot.n.cn/chat"
        
        nt = f"{app_name}{ver}{lang}{platform}{self.ua}{width}x{height}{color_depth}{referrer}"
        at = len(nt)
        it = 1
        while it:
            nt += str(it ^ at)
            it -= 1
            at += 1
        
        return (round(random.random() * 2147483647) ^ self._e(nt)) * 2147483647
    
    def generate_mid(self):
        """生成 MID"""
        domain = "https://bot.n.cn"
        epoch_ms = int(self._get_effective_epoch_seconds() * 1000)
        rt = (
            str(self._e(domain))
            + str(self.generate_unique_hash())
            + str(epoch_ms + random.random() + random.random())
        )
        formatted_rt = rt.replace('.', 'e')[:32]
        return formatted_rt

    def get_iso8601_time(self, epoch_seconds: Optional[float] = None):
        """获取 ISO8601 时间格式（固定+08:00）。

        注意：在Vercel等环境中，系统时区可能为UTC；这里不依赖系统TZ。
        """

        epoch_seconds = self._get_effective_epoch_seconds() if epoch_seconds is None else epoch_seconds
        dt = datetime.fromtimestamp(epoch_seconds, tz=timezone(timedelta(hours=8)))
        return dt.strftime('%Y-%m-%dT%H:%M:%S') + '+08:00'
    
    def get_headers(self):
        """生成请求头"""
        device = "Web"
        ver = "1.2"
        timestamp = self.get_iso8601_time()
        access_token = self.generate_mid()
        zm_ua = self.md5(self.ua)
        
        zm_token_str = f"{device}{timestamp}{ver}{access_token}{zm_ua}"
        zm_token = self.md5(zm_token_str)
        
        return {
            'device-platform': device,
            'timestamp': timestamp,
            'access-token': access_token,
            'zm-token': zm_token,
            'zm-ver': ver,
            'zm-ua': zm_ua,
            'User-Agent': self.ua
        }
    
    def http_get(self, url, headers, timeout=None, retry_count=None):
        """使用标准库发送 GET 请求，支持重试和代理"""
        # 使用默认配置或参数传入的配置
        timeout = timeout or self.http_timeout
        retry_count = retry_count if retry_count is not None else self.retry_count
        
        # 构建请求对象
        req = urllib.request.Request(url, headers=headers)
        
        # 配置代理
        if self.proxy_url:
            proxy_handler = urllib.request.ProxyHandler({'http': self.proxy_url, 'https': self.proxy_url})
            opener = urllib.request.build_opener(proxy_handler)
            self.logger.debug(f"使用代理: {self.proxy_url}")
        else:
            opener = urllib.request.build_opener()
        
        # 配置SSL验证
        if not self.ssl_verify:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            opener.add_handler(urllib.request.HTTPSHandler(context=ssl_context))
            self.logger.debug("SSL证书验证已禁用")
        
        for attempt in range(retry_count + 1):
            try:
                with opener.open(req, timeout=timeout) as response:
                    response_data = response.read().decode('utf-8')
                    
                    # 检查响应状态码
                    if response.getcode() >= 400:
                        raise Exception(f"HTTP错误状态码: {response.getcode()}")
                    
                    self.logger.debug(f"HTTP GET请求成功 (尝试 {attempt + 1}): {len(response_data)} bytes")
                    return response_data
                    
            except urllib.error.HTTPError as e:
                error_msg = f"HTTP GET请求失败 (尝试 {attempt + 1}) - HTTP错误: {e.code} - {e.reason}"
                self.logger.warning(error_msg)
                
                # 如果是客户端错误（4xx），不重试
                if 400 <= e.code < 500:
                    raise Exception(f"HTTP GET请求失败: {e.code} - {e.reason}")
                
                # 服务器错误（5xx）可以重试
                if attempt < retry_count:
                    self.logger.info(f"将在2秒后重试...")
                    time.sleep(2)
                    continue
                else:
                    self.logger.error(error_msg, exc_info=True)
                    raise Exception(f"HTTP GET请求失败: {e.code} - {e.reason}")
                    
            except urllib.error.URLError as e:
                error_msg = f"HTTP GET请求失败 (尝试 {attempt + 1}) - URL错误: {e.reason}"
                self.logger.warning(error_msg)
                
                if attempt < retry_count:
                    self.logger.info(f"将在2秒后重试...")
                    time.sleep(2)
                    continue
                else:
                    self.logger.error(error_msg, exc_info=True)
                    raise Exception(f"HTTP GET请求失败: {e.reason}")
                    
            except Exception as e:
                error_msg = f"HTTP GET请求失败 (尝试 {attempt + 1}) - 未知错误: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                
                if attempt < retry_count:
                    self.logger.info(f"将在2秒后重试...")
                    time.sleep(2)
                    continue
                else:
                    raise Exception(f"HTTP GET请求失败: {str(e)}")
        
        # 理论上不会到达这里
        raise Exception("所有重试尝试均失败")
    
    def http_post(self, url, data, headers, timeout=None, retry_count=None, return_headers: bool = False):
        """使用标准库发送 POST 请求，支持重试和代理"""
        # 使用默认配置或参数传入的配置
        timeout = timeout or self.http_timeout
        retry_count = retry_count if retry_count is not None else self.retry_count
        
        data_bytes = data.encode('utf-8')
        
        # 构建请求对象
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method='POST')
        
        # 配置代理
        if self.proxy_url:
            proxy_handler = urllib.request.ProxyHandler({'http': self.proxy_url, 'https': self.proxy_url})
            opener = urllib.request.build_opener(proxy_handler)
            self.logger.debug(f"使用代理: {self.proxy_url}")
        else:
            opener = urllib.request.build_opener()
        
        # 配置SSL验证
        if not self.ssl_verify:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            opener.add_handler(urllib.request.HTTPSHandler(context=ssl_context))
            self.logger.debug("SSL证书验证已禁用")
        
        for attempt in range(retry_count + 1):
            try:
                with opener.open(req, timeout=timeout) as response:
                    response_data = response.read()
                    response_headers = dict(response.headers.items())
                    
                    # 检查响应状态码
                    if response.getcode() >= 400:
                        raise Exception(f"HTTP错误状态码: {response.getcode()}")
                    
                    self.logger.debug(f"HTTP POST请求成功 (尝试 {attempt + 1}): {len(response_data)} bytes")
                    if return_headers:
                        return response_data, response_headers
                    return response_data
                    
            except urllib.error.HTTPError as e:
                error_msg = f"HTTP POST请求失败 (尝试 {attempt + 1}) - HTTP错误: {e.code} - {e.reason}"
                self.logger.warning(error_msg)
                
                # 如果是客户端错误（4xx），不重试
                if 400 <= e.code < 500:
                    # 尝试读取错误响应体
                    try:
                        error_body = e.read().decode('utf-8', errors='replace')
                        self.logger.error(f"错误响应体: {error_body[:500]}")
                    except:
                        pass
                    raise Exception(f"HTTP POST请求失败: {e.code} - {e.reason}")
                
                # 服务器错误（5xx）可以重试
                if attempt < retry_count:
                    self.logger.info(f"将在2秒后重试...")
                    time.sleep(2)
                    continue
                else:
                    self.logger.error(error_msg, exc_info=True)
                    raise Exception(f"HTTP POST请求失败: {e.code} - {e.reason}")
                    
            except urllib.error.URLError as e:
                error_msg = f"HTTP POST请求失败 (尝试 {attempt + 1}) - URL错误: {e.reason}"
                self.logger.warning(error_msg)
                
                if attempt < retry_count:
                    self.logger.info(f"将在2秒后重试...")
                    time.sleep(2)
                    continue
                else:
                    self.logger.error(error_msg, exc_info=True)
                    raise Exception(f"HTTP POST请求失败: {e.reason}")
                    
            except Exception as e:
                error_msg = f"HTTP POST请求失败 (尝试 {attempt + 1}) - 未知错误: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                
                if attempt < retry_count:
                    self.logger.info(f"将在2秒后重试...")
                    time.sleep(2)
                    continue
                else:
                    raise Exception(f"HTTP POST请求失败: {str(e)}")
        
        # 理论上不会到达这里
        raise Exception("所有重试尝试均失败")
    
    def load_voices(self):
        """加载声音列表"""
        filename = os.path.join(self.cache_dir, 'robots.json')  # 使用配置的缓存目录
        
        try:
            # 首先尝试从缓存文件加载
            if os.path.exists(filename):
                self.logger.info(f"从缓存文件加载声音列表: {filename}")
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 验证缓存数据格式
                    if self._validate_voice_data(data):
                        self.voices.clear()
                        for item in data['data']['list']:
                            self.voices[item['tag']] = {
                                'name': item['title'],
                                'iconUrl': item['icon']
                            }
                        self.logger.info(f"从缓存成功加载 {len(self.voices)} 个声音模型")
                        return
                    else:
                        self.logger.warning("缓存文件数据格式不正确，将重新从网络获取")
                        
                except Exception as e:
                    self.logger.warning(f"加载缓存文件失败: {str(e)}")
            
            # 从网络获取声音列表
            self.logger.info("从网络获取声音列表...")
            api_url = 'https://bot.n.cn/api/robot/platform'
            
            for attempt in range(3):  # 最多尝试3次
                try:
                    self.sync_time_offset()
                    headers = self.get_headers()
                    response_text = self.http_get(api_url, headers)
                    data = json.loads(response_text)
                    
                    if self._validate_voice_data(data):
                        # 保存到缓存文件
                        try:
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            self.logger.info(f"声音列表已缓存到: {filename}")
                        except Exception as e:
                            self.logger.warning(f"保存缓存文件失败: {str(e)}")
                        
                        # 清空旧的声音列表并更新
                        self.voices.clear()
                        for item in data['data']['list']:
                            self.voices[item['tag']] = {
                                'name': item['title'],
                                'iconUrl': item['icon']
                            }
                        self.logger.info(f"从网络成功加载 {len(self.voices)} 个声音模型")
                        return
                    else:
                        raise Exception("API返回的数据格式不正确")
                        
                except Exception as e:
                    self.logger.warning(f"网络获取声音列表失败 (尝试 {attempt + 1}): {str(e)}")
                    if attempt < 2:  # 不是最后一次尝试
                        time.sleep(2)  # 等待2秒后重试
                    else:
                        raise
                        
        except Exception as e:
            self.logger.error(f"加载声音列表失败: {str(e)}", exc_info=True)
            self.voices.clear()
            # 如果网络请求失败，添加默认选项
            self.voices['DeepSeek'] = {'name': 'DeepSeek (默认)', 'iconUrl': ''}
            self.logger.warning("使用默认声音模型")
    
    def _validate_voice_data(self, data):
        """验证声音数据格式"""
        try:
            return (
                isinstance(data, dict) and
                'data' in data and
                isinstance(data['data'], dict) and
                'list' in data['data'] and
                isinstance(data['data']['list'], list) and
                len(data['data']['list']) > 0
            )
        except Exception:
            return False
    
    def split_text(self, text, max_chars=500):
        """
        智能分割文本，尽量在标点处分割
        """
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        separators = ['。', '！', '？', '；', '\n', '.', '!', '?', ';']
        
        i = 0
        while i < len(text):
            if i + max_chars >= len(text):
                chunks.append(text[i:])
                break
            
            split_pos = -1
            search_end = min(i + max_chars, len(text))
            
            for j in range(search_end - 1, i + max_chars // 2, -1):
                if text[j] in separators:
                    split_pos = j + 1
                    break
            
            if split_pos == -1:
                split_pos = i + max_chars
            
            chunks.append(text[i:split_pos])
            i = split_pos
        
        return chunks
    
    def merge_audio_files(self, audio_data_list):
        """
        合并多个音频文件数据 (bytes)
        """
        if not audio_data_list:
            return b""
        
        if len(audio_data_list) == 1:
            return audio_data_list[0]
        
        if AudioSegment is None:
            self.logger.warning("pydub 未安装，无法智能合并音频，将使用直接拼接（可能会有杂音）")
            return b"".join(audio_data_list)
        
        try:
            combined = AudioSegment.empty()
            for data in audio_data_list:
                if not data:
                    continue
                segment = AudioSegment.from_mp3(io.BytesIO(data))
                combined += segment
            
            output = io.BytesIO()
            combined.export(output, format="mp3")
            return output.getvalue()
        except Exception as e:
            self.logger.error(f"合并音频失败: {str(e)}，尝试直接拼接", exc_info=True)
            return b"".join(audio_data_list)
    
    def process_long_text(self, text, voice, speed, pitch, volume, language, gender, timeout, retry_count):
        """处理长文本：分割、生成、合并"""
        chunks = self.split_text(text, max_chars=500)
        self.logger.info(f"文本过长({len(text)}字符)，已分割为 {len(chunks)} 个片段处理")
        
        max_workers = 3
        audio_segments = [None] * len(chunks)
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_index = {
                    executor.submit(
                        self.get_audio,
                        chunk, voice, speed, pitch, volume, language, gender, timeout, retry_count
                    ): i
                    for i, chunk in enumerate(chunks)
                }
                
                for future in concurrent.futures.as_completed(future_to_index):
                    i = future_to_index[future]
                    try:
                        data = future.result()
                        audio_segments[i] = data
                        self.logger.info(f"片段 {i+1}/{len(chunks)} 处理完成")
                    except Exception as e:
                        self.logger.error(f"片段 {i+1} 处理失败: {str(e)}")
                        raise
                
            self.logger.info(f"所有片段处理完成，正在合并...")
            return self.merge_audio_files(audio_segments)
        
        except Exception as e:
            self.logger.error(f"处理长文本失败: {str(e)}", exc_info=True)
            raise
    
    def get_audio(self, text, voice='DeepSeek', speed=1.0, pitch=1.0, volume=1.0, language=None, gender=None, timeout=60, retry_count=2):
        """获取音频"""
        if not text or not text.strip():
            raise ValueError("文本不能为空")

        if voice not in self.voices:
            raise ValueError(f"不支持的声音模型: {voice}")

        # 检查是否需要分割文本
        max_chars = 500
        if len(text) > max_chars:
            return self.process_long_text(text, voice, speed, pitch, volume, language, gender, timeout, retry_count)

        url = f'https://bot.n.cn/api/tts/v1?roleid={voice}'

        # 构建 form_data
        params = [
            f'text={urllib.parse.quote(text)}',
            'audio_type=mp3',
            'format=stream'
        ]

        # 添加新参数
        if speed != 1.0:
            params.append(f'speed={speed}')
        if pitch != 1.0:
            params.append(f'pitch={pitch}')
        if volume != 1.0:
            params.append(f'volume={volume}')
        if language:
            params.append(f'language={language}')
        if gender:
            params.append(f'gender={gender}')

        form_data = '&' + '&'.join(params)

        for attempt in range(retry_count + 1):
            try:
                # 在每次请求前做一次时间偏差检查（缓存间隔内不会重复网络请求）
                self.sync_time_offset()

                headers = self.get_headers()
                headers['Content-Type'] = 'application/x-www-form-urlencoded'

                request_timestamp = headers.get('timestamp')
                time_status = self.get_time_sync_status()

                self.logger.info(
                    "开始生成音频 - 模型: %s, 文本长度: %s (尝试 %s/%s), timestamp=%s, offset=%s",
                    voice,
                    len(text),
                    attempt + 1,
                    retry_count + 1,
                    request_timestamp,
                    time_status.get('offset_seconds'),
                )

                start_time = time.time()
                audio_data, response_headers = self.http_post(
                    url,
                    form_data,
                    headers,
                    timeout=timeout,
                    retry_count=0,
                    return_headers=True,
                )
                end_time = time.time()
                duration = end_time - start_time

                date_header = response_headers.get('Date') or response_headers.get('date')
                server_timing = response_headers.get('Server-Timing') or response_headers.get('server-timing')
                server_epoch = self._parse_http_date_to_epoch(date_header) if date_header else None

                if server_epoch is not None:
                    local_midpoint = (start_time + end_time) / 2
                    offset = server_epoch - local_midpoint

                    self._time_offset_seconds = offset
                    self._time_offset_checked_at = end_time
                    self._last_server_epoch_seconds = server_epoch
                    self._last_server_date_header = date_header
                    self._last_time_sync_error = None

                self._last_request_time_info = {
                    "request_timestamp": request_timestamp,
                    "local_start_epoch": start_time,
                    "local_end_epoch": end_time,
                    "duration_seconds": duration,
                    "response_date_header": date_header,
                    "response_server_timing": server_timing,
                    "server_epoch_seconds": server_epoch,
                    "offset_seconds": self._time_offset_seconds,
                    "threshold_seconds": self.time_drift_threshold_seconds,
                }

                self.logger.debug(
                    "API响应时间: %.2f秒, 响应大小: %s字节, response_date=%s, server_timing=%s, offset=%s",
                    duration,
                    len(audio_data),
                    date_header,
                    server_timing,
                    self._time_offset_seconds,
                )

                # 检查响应内容
                first_16_hex = audio_data[:16].hex()
                is_json_response = audio_data.startswith((b'{', b'['))

                if is_json_response:
                    try:
                        json_response = json.loads(audio_data.decode('utf-8', errors='replace'))
                        error_code_raw = json_response.get('code', 'unknown')
                        error_code = str(error_code_raw)
                        error_message = json_response.get('message', json_response.get('msg', 'unknown'))

                        # 根据错误代码提供更具体的错误信息
                        if error_code == '110023':
                            error_detail = "设备时间异常（timestamp与服务器时间偏差过大，签名校验失败）"
                        elif error_code in ['40001', '40002']:
                            error_detail = "请求参数错误，请检查文本内容和模型名称"
                        elif error_code in ['50001', '50002']:
                            error_detail = "服务器内部错误，请稍后重试"
                        else:
                            error_detail = f"API错误代码: {error_code}, 错误信息: {error_message}"

                        self.logger.error(f"API返回错误响应: {json_response}")
                        self.logger.error(f"错误诊断: {error_detail}")

                        if error_code == '110023':
                            self.logger.error(
                                "110023时间诊断: time_status=%s, last_request=%s",
                                self.get_time_sync_status(),
                                self._last_request_time_info,
                            )

                            if attempt < retry_count:
                                self.logger.info(
                                    "检测到110023设备时间异常，将在2秒后重试，并强制刷新时间偏差..."
                                )
                                time.sleep(2)
                                self.sync_time_offset(force=True)
                                continue

                        raise Exception(f"上游API错误: {error_detail}")

                    except json.JSONDecodeError:
                        self.logger.warning(f"收到JSON格式响应但无法解析: {first_16_hex}")
                        # 继续处理，可能是非标准JSON格式

                is_valid, msg, normalized_audio, debug = validate_and_normalize_mp3(audio_data)
                if not is_valid:
                    preview = normalized_audio[:200]
                    preview_text = preview.decode('utf-8', errors='replace')

                    trimmed = normalized_audio.lstrip()
                    if trimmed.startswith((b'{', b'[')):
                        try:
                            parsed = json.loads(trimmed.decode('utf-8'))
                            raise Exception(f"上游返回JSON而非MP3: {parsed}")
                        except Exception:
                            pass

                    if trimmed.startswith(b'<'):
                        raise Exception(f"上游返回HTML而非MP3，预览: {preview_text}")

                    # 如果不是最后一次尝试，且错误可能由于网络问题引起，则重试
                    if attempt < retry_count and "未检测到MP3同步帧" in msg:
                        self.logger.warning(f"音频格式验证失败，将重试: {msg}")
                        time.sleep(2)
                        continue

                    raise Exception(
                        f"返回的音频数据不是有效MP3: {msg}; first16={debug.get('first16_hex')}; 响应预览: {preview_text[:100]}"
                    )

                if debug.get('decompressed'):
                    self.logger.info(
                        f"检测到gzip压缩内容并已解压: {debug.get('original_len')} -> {debug.get('normalized_len')} 字节"
                    )

                if debug.get('trimmed_offset'):
                    self.logger.warning(
                        f"MP3同步帧不在开头，已自动裁剪前置数据: offset={debug.get('trimmed_offset')}"
                    )

                self.logger.info(
                    "音频生成成功 - 数据大小: %s 字节; 校验: %s; first16=%s; 总耗时: %.2f秒",
                    len(normalized_audio),
                    msg,
                    debug.get('first16_hex'),
                    duration,
                )
                return normalized_audio

            except Exception as e:
                self.logger.error(f"获取音频失败 (尝试 {attempt + 1}): {str(e)}", exc_info=True)

                # 如果是最后一次尝试，或者错误不太可能通过重试解决，则抛出异常
                if attempt == retry_count or "不支持的声音模型" in str(e) or "文本不能为空" in str(e):
                    raise

                # 网络错误或其他可能的问题，等待后重试
                wait_time = 2 * (attempt + 1)  # 指数退避
                self.logger.info(f"将在{wait_time}秒后重试...")
                time.sleep(wait_time)

        # 理论上不应该到达这里
        raise Exception("所有重试尝试均失败")
