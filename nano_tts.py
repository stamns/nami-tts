import urllib.request
import urllib.parse
import hashlib
import json
import os
import logging
import gzip
import ssl
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import random
import time


def _find_mp3_sync_offset(data: bytes, max_scan: int = 4096) -> Optional[int]:
    if not data or len(data) < 2:
        return None

    scan_len = min(len(data), max_scan)
    for i in range(scan_len - 1):
        if data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0:
            return i
    return None


def _parse_id3v2_tag_size(data: bytes) -> Optional[int]:
    if len(data) < 10 or not data.startswith(b"ID3"):
        return None

    # ID3v2 size is a 4-byte syncsafe integer at bytes 6..9
    size_bytes = data[6:10]
    if any(b & 0x80 for b in size_bytes):
        return None

    size = (size_bytes[0] << 21) | (size_bytes[1] << 14) | (size_bytes[2] << 7) | size_bytes[3]
    return 10 + size


def _validate_and_normalize_mp3(data: bytes) -> Tuple[bool, str, bytes, Dict[str, Any]]:
    debug: Dict[str, Any] = {
        "original_len": 0 if not data else len(data),
        "decompressed": False,
        "id3_present": False,
        "id3_declared_end": None,
        "first_sync_offset": None,
        "trimmed_offset": None,
        "normalized_len": 0,
        "first16_hex": "" if not data else data[:16].hex(),
    }

    if not data:
        return False, "音频数据为空", b"", debug

    if len(data) >= 2 and data[0] == 0x1F and data[1] == 0x8B:
        try:
            decompressed = gzip.decompress(data)
            debug["decompressed"] = True
            data = decompressed
            debug["first16_hex"] = data[:16].hex()
        except Exception:
            # 如果误判为gzip，直接继续后续校验
            pass

    if data.startswith(b"ID3"):
        debug["id3_present"] = True
        id3_end = _parse_id3v2_tag_size(data)
        debug["id3_declared_end"] = id3_end

        if id3_end is not None and id3_end < len(data):
            if data[id3_end] == 0xFF and (data[id3_end + 1] & 0xE0) == 0xE0:
                debug["first_sync_offset"] = id3_end
                debug["normalized_len"] = len(data)
                return True, "有效的MP3文件(ID3标签)", data, debug

    sync_offset = _find_mp3_sync_offset(data)
    debug["first_sync_offset"] = sync_offset

    if sync_offset is None:
        debug["normalized_len"] = len(data)
        return False, "未检测到MP3同步帧", data, debug

    if sync_offset > 0:
        data = data[sync_offset:]
        debug["trimmed_offset"] = sync_offset
        debug["first16_hex"] = data[:16].hex()

    debug["normalized_len"] = len(data)
    return True, "有效的MP3文件(包含同步帧)", data, debug


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
        self.cache_dir = os.getenv('CACHE_DIR', 'cache')
        self.http_timeout = int(os.getenv('HTTP_TIMEOUT', '30'))
        self.retry_count = int(os.getenv('RETRY_COUNT', '2'))
        self.proxy_url = os.getenv('PROXY_URL', '').strip()
        self.ssl_verify = os.getenv('SSL_VERIFY', 'true').lower() in ('true', '1', 'yes', 'on')
        
        self.logger.info(f"TTS引擎配置: timeout={self.http_timeout}s, retry={self.retry_count}, proxy={bool(self.proxy_url)}, ssl_verify={self.ssl_verify}")
        
        self._ensure_cache_dir()  # 确保缓存目录存在
        self.load_voices()
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir, exist_ok=True)
                self.logger.info(f"创建缓存目录: {self.cache_dir}")
        except Exception as e:
            self.logger.error(f"创建缓存目录失败: {str(e)}", exc_info=True)
    
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
        rt = str(self._e(domain)) + str(self.generate_unique_hash()) + str(int(time.time() * 1000) + random.random() + random.random())
        formatted_rt = rt.replace('.', 'e')[:32]
        return formatted_rt
    
    def get_iso8601_time(self):
        """获取 ISO8601 时间格式"""
        now = datetime.now()
        return now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
    
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
    
    def http_post(self, url, data, headers, timeout=None, retry_count=None):
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
                    
                    # 检查响应状态码
                    if response.getcode() >= 400:
                        raise Exception(f"HTTP错误状态码: {response.getcode()}")
                    
                    self.logger.debug(f"HTTP POST请求成功 (尝试 {attempt + 1}): {len(response_data)} bytes")
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
            headers = self.get_headers()
            
            for attempt in range(3):  # 最多尝试3次
                try:
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
    
    def get_audio(self, text, voice='DeepSeek', timeout=60, retry_count=2):
        """获取音频"""
        if not text or not text.strip():
            raise ValueError("文本不能为空")
        
        if voice not in self.voices:
            raise ValueError(f"不支持的声音模型: {voice}")
        
        url = f'https://bot.n.cn/api/tts/v1?roleid={voice}'
        
        headers = self.get_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        # 限制文本长度，避免请求过大
        max_length = 1000
        original_length = len(text)
        if len(text) > max_length:
            self.logger.warning(f"文本长度超过限制({max_length})，将被截断: {original_length} -> {max_length}")
            text = text[:max_length]
        
        form_data = f'&text={urllib.parse.quote(text)}&audio_type=mp3&format=stream'
        
        for attempt in range(retry_count + 1):
            try:
                self.logger.info(f"开始生成音频 - 模型: {voice}, 文本长度: {len(text)} (尝试 {attempt + 1}/{retry_count + 1})")
                
                start_time = time.time()
                audio_data = self.http_post(url, form_data, headers, timeout=timeout)
                duration = time.time() - start_time

                self.logger.debug(f"API响应时间: {duration:.2f}秒, 响应大小: {len(audio_data)}字节")

                # 检查响应内容
                first_16_hex = audio_data[:16].hex()
                is_json_response = audio_data.startswith((b'{', b'['))
                
                if is_json_response:
                    try:
                        json_response = json.loads(audio_data.decode('utf-8', errors='replace'))
                        error_code = json_response.get('code', 'unknown')
                        error_message = json_response.get('message', json_response.get('msg', 'unknown'))
                        
                        # 根据错误代码提供更具体的错误信息
                        if error_code == '110023':
                            error_detail = "API认证失败或权限不足，请检查API密钥配置"
                        elif error_code in ['40001', '40002']:
                            error_detail = "请求参数错误，请检查文本内容和模型名称"
                        elif error_code in ['50001', '50002']:
                            error_detail = "服务器内部错误，请稍后重试"
                        else:
                            error_detail = f"API错误代码: {error_code}, 错误信息: {error_message}"
                        
                        self.logger.error(f"API返回错误响应: {json_response}")
                        self.logger.error(f"错误诊断: {error_detail}")
                        
                        # 如果是认证错误且不是最后一次尝试，等待后重试
                        if error_code == '110023' and attempt < retry_count:
                            self.logger.info("检测到认证错误，将在5秒后重试...")
                            time.sleep(5)
                            continue
                        else:
                            raise Exception(f"上游API错误: {error_detail}")
                            
                    except json.JSONDecodeError:
                        self.logger.warning(f"收到JSON格式响应但无法解析: {first_16_hex}")
                        # 继续处理，可能是非标准JSON格式

                is_valid, msg, normalized_audio, debug = _validate_and_normalize_mp3(audio_data)
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

                    raise Exception(f"返回的音频数据不是有效MP3: {msg}; first16={debug.get('first16_hex')}; 响应预览: {preview_text[:100]}")

                if debug.get('decompressed'):
                    self.logger.info(
                        f"检测到gzip压缩内容并已解压: {debug.get('original_len')} -> {debug.get('normalized_len')} 字节"
                    )

                if debug.get('trimmed_offset'):
                    self.logger.warning(
                        f"MP3同步帧不在开头，已自动裁剪前置数据: offset={debug.get('trimmed_offset')}"
                    )

                self.logger.info(
                    f"音频生成成功 - 数据大小: {len(normalized_audio)} 字节; 校验: {msg}; first16={debug.get('first16_hex')}; 总耗时: {duration:.2f}秒"
                )
                return normalized_audio
                
            except Exception as e:
                self.logger.error(f"获取音频失败 (尝试 {attempt + 1}): {str(e)}", exc_info=True)
                
                # 如果是最后一次尝试，或者错误不太可能通过重试解决，则抛出异常
                if attempt == retry_count or "不支持的声音模型" in str(e) or "文本不能为空" in str(e):
                    raise
                else:
                    # 网络错误或其他可能的问题，等待后重试
                    wait_time = 2 * (attempt + 1)  # 指数退避
                    self.logger.info(f"将在{wait_time}秒后重试...")
                    time.sleep(wait_time)
        
        # 理论上不应该到达这里
        raise Exception("所有重试尝试均失败")
