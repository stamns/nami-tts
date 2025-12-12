import urllib.request
import urllib.parse
import hashlib
import json
import os
import logging
from datetime import datetime
import random
import time
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
        self.cache_dir = os.getenv('CACHE_DIR', 'cache')  # 缓存目录支持环境变量配置
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
    
    def http_get(self, url, headers):
        """使用标准库发送 GET 请求"""
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTP GET请求失败 - HTTP错误: {e.code} - {e.reason}", exc_info=True)
            raise Exception(f"HTTP GET请求失败: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            self.logger.error(f"HTTP GET请求失败 - URL错误: {e.reason}", exc_info=True)
            raise Exception(f"HTTP GET请求失败: {e.reason}")
        except Exception as e:
            self.logger.error(f"HTTP GET请求失败 - 未知错误: {str(e)}", exc_info=True)
            raise Exception(f"HTTP GET请求失败: {str(e)}")
    
    def http_post(self, url, data, headers):
        """使用标准库发送 POST 请求"""
        data_bytes = data.encode('utf-8')
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTP POST请求失败 - HTTP错误: {e.code} - {e.reason}", exc_info=True)
            raise Exception(f"HTTP POST请求失败: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            self.logger.error(f"HTTP POST请求失败 - URL错误: {e.reason}", exc_info=True)
            raise Exception(f"HTTP POST请求失败: {e.reason}")
        except Exception as e:
            self.logger.error(f"HTTP POST请求失败 - 未知错误: {str(e)}", exc_info=True)
            raise Exception(f"HTTP POST请求失败: {str(e)}")
    
    def load_voices(self):
        """加载声音列表"""
        filename = os.path.join(self.cache_dir, 'robots.json')  # 使用配置的缓存目录
        
        try:
            # 首先尝试从缓存文件加载
            if os.path.exists(filename):
                self.logger.info(f"从缓存文件加载声音列表: {filename}")
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                self.logger.info("从网络获取声音列表...")
                response_text = self.http_get('https://bot.n.cn/api/robot/platform', self.get_headers())
                data = json.loads(response_text)
                
                # 保存到缓存文件
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    self.logger.info(f"声音列表已缓存到: {filename}")
                except Exception as e:
                    self.logger.warning(f"保存缓存文件失败: {str(e)}")
            
            # 清空旧的声音列表
            self.voices.clear()
            if 'data' in data and 'list' in data['data']:
                for item in data['data']['list']:
                    self.voices[item['tag']] = {
                        'name': item['title'],
                        'iconUrl': item['icon']
                    }
                self.logger.info(f"成功加载 {len(self.voices)} 个声音模型")
            else:
                self.logger.warning("API返回的数据格式不正确")
                raise Exception("API返回的数据格式不正确")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"解析JSON数据失败: {str(e)}", exc_info=True)
            raise Exception(f"解析JSON数据失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"加载声音列表失败: {str(e)}", exc_info=True)
            self.voices.clear()
            # 如果网络请求失败，添加默认选项
            self.voices['DeepSeek'] = {'name': 'DeepSeek (默认)', 'iconUrl': ''}
            self.logger.warning("使用默认声音模型")
    
    def get_audio(self, text, voice='DeepSeek'):
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
        if len(text) > max_length:
            self.logger.warning(f"文本长度超过限制({max_length})，将被截断")
            text = text[:max_length]
        
        form_data = f'&text={urllib.parse.quote(text)}&audio_type=mp3&format=stream'
        
        try:
            self.logger.info(f"开始生成音频 - 模型: {voice}, 文本长度: {len(text)}")
            audio_data = self.http_post(url, form_data, headers)
            
            # ✅ 修复后的智能验证逻辑
            if not audio_data or len(audio_data) < 50:
            # 更宽松的验证条件 (Vercel环境适配)
                self.logger.warning(f"音频数据可能不完整: 长度={len(audio_data)}字节")
            # 尝试检查是否是有效的MP3文件头 (ID3标签或MP3帧头)
                if audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xe3'):
                   self.logger.info("检测到有效MP3文件头，忽略长度检查")
                else:
                   raise Exception("返回的音频数据无效")

            
            self.logger.info(f"音频生成成功 - 数据大小: {len(audio_data)} 字节")
            return audio_data
            
        except Exception as e:
            self.logger.error(f"获取音频失败: {str(e)}", exc_info=True)
            raise
