# 使用示例 - NanoAI TTS 实战教程

[![返回 README](https://img.shields.io/badge/返回-README--CN-blue?style=flat-square)](./README-CN.md)
[![部署指南](https://img.shields.io/badge/部署-DEPLOYMENT--CN-green?style=flat-square)](./DEPLOYMENT-CN.md)
[![FAQ](https://img.shields.io/badge/常见问题-FAQ--CN-orange?style=flat-square)](./FAQ-CN.md)

本文档通过多个实际使用场景，演示如何有效使用 NanoAI TTS 服务。

## 📋 目录

- [快速开始](#快速开始)
- [Web 界面使用](#web-界面使用)
- [Python 集成](#python-集成)
- [JavaScript 集成](#javascript-集成)
- [实战场景](#实战场景)
- [批量处理](#批量处理)
- [高级技巧](#高级技巧)

## 🚀 快速开始

### 最简单的用法

```python
import requests

# 生成一句话的音频
response = requests.post('http://localhost:5001/v1/audio/speech', json={
    'input': '你好，世界',
    'model': 'DeepSeek',
})

# 保存为 MP3 文件
with open('hello.mp3', 'wb') as f:
    f.write(response.content)
```

### Web 界面使用

1. 打开 http://localhost:5001
2. 在文本框中输入要转换的文本
3. 选择语言和性别
4. 点击"生成音频"按钮
5. 点击播放或下载

## 🌐 Web 界面使用

### 基本操作

#### 步骤 1：输入文本

在主页的文本框中输入你要转换的文本。最简单的例子：

```
你好，欢迎使用 NanoAI TTS 服务。
```

#### 步骤 2：调整参数

使用右侧的参数面板：

- **语言**: 选择"简体中文"
- **性别**: 选择"女"或"男"
- **速度**: 拖动滑条调整（1.0 为正常速度）
- **音调**: 调整声音高低
- **音量**: 调整音频大小

#### 步骤 3：生成和下载

点击"生成音频"按钮，等待几秒钟后：

- 在播放器中播放生成的音频
- 点击"下载"按钮下载 MP3 文件
- 点击"复制链接"复制分享链接

### 高级功能

#### 批量转换

对于多个句子，可以：

1. 每个句子生成一个音频
2. 使用音频编辑软件拼接
3. 或者将多个句子一起输入（系统会自动处理）

#### 对比不同参数

生成相同文本的不同版本：

- **正常速度**: speed = 1.0
- **快速**: speed = 1.5（适合快速浏览）
- **慢速**: speed = 0.75（适合学习）

## 🐍 Python 集成

### 安装依赖

```bash
pip install requests python-dotenv
```

### 基础示例

#### 例 1：简单的文本转语音

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# 服务 URL
BASE_URL = os.getenv('TTS_API_URL', 'http://localhost:5001')

# 发送请求
response = requests.post(f'{BASE_URL}/v1/audio/speech', json={
    'input': '这是一个测试句子。',
    'model': 'DeepSeek',
    'language': 'zh-CN',
})

# 保存文件
if response.status_code == 200:
    with open('test.mp3', 'wb') as f:
        f.write(response.content)
    print("✓ 音频生成成功：test.mp3")
else:
    print(f"✗ 错误: {response.status_code}")
    print(response.text)
```

#### 例 2：生成有声书

```python
import requests
import os

# 小说文本（来自文件）
with open('novel.txt', 'r', encoding='utf-8') as f:
    novel_text = f.read()

# API 参数
params = {
    'input': novel_text,
    'model': 'DeepSeek',
    'language': 'zh-CN',
    'gender': 'female',
    'speed': 1.0,
}

# 生成音频
response = requests.post('http://localhost:5001/v1/audio/speech', json=params)

if response.status_code == 200:
    # 长文本会返回 ZIP 或 M3U8
    content_type = response.headers.get('content-type', '')
    
    if 'zip' in content_type:
        # 保存为 ZIP
        with open('audiobook.zip', 'wb') as f:
            f.write(response.content)
        print("✓ 有声书生成完毕：audiobook.zip")
    else:
        # 保存为单个 MP3
        with open('audiobook.mp3', 'wb') as f:
            f.write(response.content)
        print("✓ 有声书生成完毕：audiobook.mp3")
```

#### 例 3：多语言支持

```python
import requests

texts = {
    'zh-CN': '你好，世界',
    'en-US': 'Hello, world',
    'ja-JP': 'こんにちは、世界',
    'ko-KR': '안녕하세요, 세상',
}

for lang_code, text in texts.items():
    response = requests.post('http://localhost:5001/v1/audio/speech', json={
        'input': text,
        'language': lang_code,
        'model': 'DeepSeek',
    })
    
    if response.status_code == 200:
        filename = f'audio_{lang_code}.mp3'
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✓ {lang_code}: {filename}")
```

#### 例 4：参数调优

```python
import requests

text = "这是一个需要不同参数配置的示例文本。"

# 定义不同的配置
configs = {
    'fast': {'speed': 1.5, 'pitch': 1.0},
    'normal': {'speed': 1.0, 'pitch': 1.0},
    'slow': {'speed': 0.75, 'pitch': 1.0},
    'high_pitch': {'speed': 1.0, 'pitch': 1.5},
    'low_pitch': {'speed': 1.0, 'pitch': 0.75},
}

for config_name, params in configs.items():
    response = requests.post('http://localhost:5001/v1/audio/speech', json={
        'input': text,
        'model': 'DeepSeek',
        **params
    })
    
    if response.status_code == 200:
        filename = f'audio_{config_name}.mp3'
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✓ {config_name}: {filename}")
```

#### 例 5：错误处理和重试

```python
import requests
import time

def generate_speech_with_retry(text, max_retries=3):
    """带重试的音频生成函数"""
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                'http://localhost:5001/v1/audio/speech',
                json={'input': text, 'model': 'DeepSeek'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.content
            
            elif response.status_code >= 500:
                # 服务器错误，重试
                print(f"服务器错误，正在重试... (尝试 {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)  # 指数退避
            
            else:
                # 客户端错误，不重试
                print(f"客户端错误: {response.status_code}")
                print(response.json())
                return None
        
        except requests.Timeout:
            print(f"请求超时，正在重试... (尝试 {attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        
        except Exception as e:
            print(f"错误: {e}")
            return None
    
    print("✗ 所有重试都失败")
    return None

# 使用
audio_data = generate_speech_with_retry("测试文本")
if audio_data:
    with open('output.mp3', 'wb') as f:
        f.write(audio_data)
```

### 高级 Python 示例

#### 例 6：构建 TTS 客户端类

```python
import requests
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NanoAITTSClient:
    """NanoAI TTS 客户端"""
    
    def __init__(self, api_url: str = 'http://localhost:5001'):
        self.api_url = api_url
        self.base_params = {
            'model': 'DeepSeek',
            'language': 'zh-CN',
            'gender': 'female',
        }
    
    def set_default_model(self, model: str):
        """设置默认模型"""
        self.base_params['model'] = model
    
    def set_default_language(self, language: str):
        """设置默认语言"""
        self.base_params['language'] = language
    
    def generate(self, text: str, **kwargs) -> Optional[bytes]:
        """生成音频"""
        params = {**self.base_params, **kwargs, 'input': text}
        
        try:
            response = requests.post(
                f'{self.api_url}/v1/audio/speech',
                json=params,
                timeout=60
            )
            
            if response.status_code == 200:
                logger.info(f"✓ 生成成功: {len(response.content)} 字节")
                return response.content
            else:
                logger.error(f"✗ API 错误 {response.status_code}: {response.text}")
                return None
        
        except requests.RequestException as e:
            logger.error(f"✗ 请求失败: {e}")
            return None
    
    def save(self, text: str, filename: str, **kwargs) -> bool:
        """生成并保存音频"""
        audio_data = self.generate(text, **kwargs)
        
        if audio_data:
            with open(filename, 'wb') as f:
                f.write(audio_data)
            logger.info(f"✓ 文件保存: {filename}")
            return True
        else:
            logger.error(f"✗ 生成失败")
            return False
    
    def batch_generate(self, texts: Dict[str, str], output_dir: str = '.') -> Dict[str, bool]:
        """批量生成"""
        results = {}
        
        for name, text in texts.items():
            filename = os.path.join(output_dir, f'{name}.mp3')
            results[name] = self.save(text, filename)
        
        return results
    
    def get_models(self) -> Optional[list]:
        """获取可用模型列表"""
        try:
            response = requests.get(f'{self.api_url}/v1/models')
            if response.status_code == 200:
                return response.json().get('models', [])
        except Exception as e:
            logger.error(f"✗ 获取模型列表失败: {e}")
        return None

# 使用示例
if __name__ == '__main__':
    load_dotenv()
    
    client = NanoAITTSClient('http://localhost:5001')
    
    # 生成单个音频
    client.save('你好，这是一个测试。', 'test.mp3')
    
    # 批量生成
    texts = {
        'greeting': '你好，欢迎使用 NanoAI TTS。',
        'thanks': '谢谢你的使用！',
        'goodbye': '再见！'
    }
    
    results = client.batch_generate(texts, output_dir='./output')
    print(results)
    
    # 列出可用模型
    models = client.get_models()
    if models:
        print(f"可用模型数: {len(models)}")
        for model in models[:3]:
            print(f"  - {model.get('name')}")
```

#### 例 7：处理长文本

```python
import requests
import re

def split_text(text: str, max_length: int = 500) -> list:
    """按句号、感叹号、问号分割文本"""
    # 按中文和英文标点符号分割
    sentences = re.split(r'[。！？\.\!\?]+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_length:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def generate_long_text_audio(text: str, output_file: str):
    """生成长文本音频"""
    
    chunks = split_text(text)
    print(f"文本已分为 {len(chunks)} 个部分")
    
    audio_files = []
    
    for i, chunk in enumerate(chunks, 1):
        print(f"生成第 {i}/{len(chunks)} 部分...")
        
        response = requests.post('http://localhost:5001/v1/audio/speech', json={
            'input': chunk,
            'model': 'DeepSeek',
        })
        
        if response.status_code == 200:
            chunk_file = f'chunk_{i:03d}.mp3'
            with open(chunk_file, 'wb') as f:
                f.write(response.content)
            audio_files.append(chunk_file)
        else:
            print(f"第 {i} 部分生成失败")
    
    print(f"✓ 所有部分生成完成，共 {len(audio_files)} 个音频文件")
    print(f"可以使用 ffmpeg 拼接这些文件：")
    print(f"ffmpeg -f concat -safe 0 -i filelist.txt -c copy {output_file}")

# 使用示例
if __name__ == '__main__':
    long_text = """
    这是一个很长的文本示例。
    第一段内容...
    第二段内容...
    """
    
    generate_long_text_audio(long_text, 'output.mp3')
```

## 🌐 JavaScript 集成

### 基础示例

#### 例 1：在 HTML 中使用

```html
<!DOCTYPE html>
<html>
<head>
    <title>NanoAI TTS Demo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; }
        textarea { width: 100%; height: 100px; }
        button { padding: 10px 20px; font-size: 16px; }
        audio { width: 100%; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>NanoAI TTS</h1>
    
    <textarea id="textInput" placeholder="输入要转换的文本...">你好，欢迎使用 NanoAI TTS。</textarea>
    
    <div>
        <label>语言：</label>
        <select id="language">
            <option value="zh-CN">简体中文</option>
            <option value="en-US">English</option>
            <option value="ja-JP">日本語</option>
        </select>
    </div>
    
    <div>
        <label>性别：</label>
        <select id="gender">
            <option value="female">女声</option>
            <option value="male">男声</option>
        </select>
    </div>
    
    <button onclick="generateAudio()">生成音频</button>
    
    <audio id="audioPlayer" controls></audio>
    
    <script>
        async function generateAudio() {
            const text = document.getElementById('textInput').value;
            const language = document.getElementById('language').value;
            const gender = document.getElementById('gender').value;
            
            if (!text) {
                alert('请输入文本');
                return;
            }
            
            try {
                const response = await fetch('http://localhost:5001/v1/audio/speech', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        input: text,
                        model: 'DeepSeek',
                        language: language,
                        gender: gender
                    })
                });
                
                if (response.ok) {
                    const audioBlob = await response.blob();
                    const audioUrl = URL.createObjectURL(audioBlob);
                    document.getElementById('audioPlayer').src = audioUrl;
                } else {
                    alert('生成失败: ' + response.statusText);
                }
            } catch (error) {
                alert('错误: ' + error.message);
            }
        }
    </script>
</body>
</html>
```

#### 例 2：React 组件

```jsx
import React, { useState } from 'react';

function TTSGenerator() {
    const [text, setText] = useState('你好，世界');
    const [language, setLanguage] = useState('zh-CN');
    const [gender, setGender] = useState('female');
    const [loading, setLoading] = useState(false);
    const [audioUrl, setAudioUrl] = useState(null);
    
    const generateAudio = async () => {
        setLoading(true);
        
        try {
            const response = await fetch('http://localhost:5001/v1/audio/speech', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    input: text,
                    model: 'DeepSeek',
                    language,
                    gender
                })
            });
            
            if (response.ok) {
                const audioBlob = await response.blob();
                const url = URL.createObjectURL(audioBlob);
                setAudioUrl(url);
            } else {
                alert('生成失败');
            }
        } catch (error) {
            alert('错误: ' + error.message);
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <div>
            <h1>NanoAI TTS</h1>
            
            <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="输入要转换的文本..."
                rows="5"
                style={{width: '100%'}}
            />
            
            <div>
                <label>语言: </label>
                <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                    <option value="zh-CN">简体中文</option>
                    <option value="en-US">English</option>
                    <option value="ja-JP">日本語</option>
                </select>
            </div>
            
            <div>
                <label>性别: </label>
                <select value={gender} onChange={(e) => setGender(e.target.value)}>
                    <option value="female">女声</option>
                    <option value="male">男声</option>
                </select>
            </div>
            
            <button onClick={generateAudio} disabled={loading}>
                {loading ? '生成中...' : '生成音频'}
            </button>
            
            {audioUrl && (
                <audio controls src={audioUrl} style={{display: 'block', marginTop: '20px'}} />
            )}
        </div>
    );
}

export default TTSGenerator;
```

## 🎬 实战场景

### 场景 1：制作视频配音

**目标**: 为教学视频添加中文配音

```python
import requests
import json

def generate_video_voiceover(scenes_data):
    """
    scenes_data 格式：
    [
        {'time': '0:00-0:10', 'text': '这是第一个场景...'},
        {'time': '0:10-0:20', 'text': '这是第二个场景...'},
    ]
    """
    
    output = {
        'voiceovers': []
    }
    
    for scene in scenes_data:
        response = requests.post('http://localhost:5001/v1/audio/speech', json={
            'input': scene['text'],
            'model': 'DeepSeek',
            'language': 'zh-CN',
            'gender': 'female',
            'speed': 1.0
        })
        
        if response.status_code == 200:
            # 保存音频
            audio_file = f"voiceover_{len(output['voiceovers'])}.mp3"
            with open(audio_file, 'wb') as f:
                f.write(response.content)
            
            output['voiceovers'].append({
                'time': scene['time'],
                'text': scene['text'],
                'audio_file': audio_file
            })
    
    # 保存配置
    with open('voiceover_config.json', 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 生成了 {len(output['voiceovers'])} 个配音片段")

# 使用示例
scenes = [
    {'time': '0:00-0:05', 'text': '欢迎来到今天的课程'},
    {'time': '0:05-0:15', 'text': '今天我们将学习机器学习的基础知识'},
]

generate_video_voiceover(scenes)
```

### 场景 2：生成有声电子书

```python
import requests
import os

class AudiobookGenerator:
    def __init__(self, api_url='http://localhost:5001'):
        self.api_url = api_url
    
    def generate_from_file(self, input_file, output_dir='audiobook'):
        """从文本文件生成有声书"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分章节
        chapters = content.split('## ')
        
        playlist = []
        
        for i, chapter in enumerate(chapters[1:], 1):  # 跳过第一个空章节
            # 提取章节标题
            lines = chapter.split('\n')
            title = lines[0] if lines else f'Chapter {i}'
            chapter_text = '\n'.join(lines[1:])
            
            print(f"正在生成第 {i} 章: {title}")
            
            response = requests.post(f'{self.api_url}/v1/audio/speech', json={
                'input': chapter_text,
                'model': 'DeepSeek',
                'language': 'zh-CN',
            })
            
            if response.status_code == 200:
                filename = f'chapter_{i:02d}.mp3'
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                playlist.append({
                    'chapter': i,
                    'title': title,
                    'file': filename,
                    'size': len(response.content)
                })
                
                print(f"✓ 第 {i} 章生成完毕")
            else:
                print(f"✗ 第 {i} 章生成失败")
        
        # 生成播放列表（M3U 格式）
        self._generate_m3u(output_dir, playlist)
        
        return playlist
    
    def _generate_m3u(self, output_dir, playlist):
        """生成 M3U 播放列表"""
        m3u_file = os.path.join(output_dir, 'playlist.m3u')
        
        with open(m3u_file, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for item in playlist:
                f.write(f'#EXTINF:-1,{item["title"]}\n')
                f.write(f'{item["file"]}\n')
        
        print(f"✓ 播放列表生成: {m3u_file}")

# 使用示例
generator = AudiobookGenerator()
playlist = generator.generate_from_file('novel.txt', output_dir='./audiobook')
```

### 场景 3：学习助手应用

```python
import requests

class LearningAssistant:
    """学习助手 - 帮助学生学习课程内容"""
    
    def __init__(self, api_url='http://localhost:5001'):
        self.api_url = api_url
    
    def explain_concept(self, concept_name: str, explanation: str):
        """用语音解释一个概念"""
        
        text = f"{concept_name}。{explanation}"
        
        response = requests.post(f'{self.api_url}/v1/audio/speech', json={
            'input': text,
            'model': 'DeepSeek',
            'language': 'zh-CN',
            'gender': 'female',
            'speed': 0.9,  # 稍微放慢速度便于理解
        })
        
        if response.status_code == 200:
            return response.content
        return None
    
    def generate_vocabulary_lesson(self, words: list):
        """生成词汇课程"""
        
        lesson_files = {}
        
        for word_data in words:
            word = word_data['word']
            definition = word_data['definition']
            example = word_data.get('example', '')
            
            # 生成词汇音频
            word_audio = self.explain_concept(word, definition)
            
            # 生成例句音频
            if example:
                example_audio = self.explain_concept('例句', example)
            
            lesson_files[word] = {
                'definition': word_audio,
                'example': example_audio if example else None
            }
        
        return lesson_files
    
    def generate_listening_practice(self, sentences: list):
        """生成听力练习"""
        
        audio_files = []
        
        for i, sentence in enumerate(sentences, 1):
            response = requests.post(f'{self.api_url}/v1/audio/speech', json={
                'input': sentence,
                'model': 'DeepSeek',
                'language': 'zh-CN',
            })
            
            if response.status_code == 200:
                filename = f'practice_{i}.mp3'
                with open(filename, 'wb') as f:
                    f.write(response.content)
                audio_files.append(filename)
        
        return audio_files

# 使用示例
assistant = LearningAssistant()

# 词汇学习
words = [
    {
        'word': '便捷',
        'definition': '方便快速，不复杂',
        'example': '这个新的应用程序使操作变得非常便捷。'
    },
    {
        'word': '阐述',
        'definition': '详细说明，清楚地讲解',
        'example': '教授在课堂上阐述了相对论的基本原理。'
    }
]

vocab_lesson = assistant.generate_vocabulary_lesson(words)
```

## 📦 批量处理

### 批量生成 CSV 数据

```python
import csv
import requests
import os

def batch_process_csv(csv_file, output_dir='output'):
    """
    CSV 格式：
    text,language,gender,speed
    你好,zh-CN,female,1.0
    Hello,en-US,male,1.0
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader, 1):
            text = row['text']
            language = row.get('language', 'zh-CN')
            gender = row.get('gender', 'female')
            speed = float(row.get('speed', 1.0))
            
            print(f"处理第 {i} 行: {text[:30]}...")
            
            response = requests.post('http://localhost:5001/v1/audio/speech', json={
                'input': text,
                'language': language,
                'gender': gender,
                'speed': speed,
            })
            
            if response.status_code == 200:
                filename = os.path.join(output_dir, f'audio_{i:04d}.mp3')
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"✓ 已保存: {filename}")
            else:
                print(f"✗ 失败: {response.status_code}")

# 使用
batch_process_csv('input.csv', output_dir='./audio_output')
```

## 🎯 高级技巧

### 1. 缓存优化

利用缓存提高速度：

```python
import requests
import hashlib

def get_audio_with_cache(text: str, cache_dir='cache'):
    """带缓存的音频生成"""
    
    import os
    os.makedirs(cache_dir, exist_ok=True)
    
    # 计算文本哈希作为缓存键
    text_hash = hashlib.md5(text.encode()).hexdigest()
    cache_file = os.path.join(cache_dir, f'{text_hash}.mp3')
    
    # 检查缓存
    if os.path.exists(cache_file):
        print(f"✓ 使用缓存")
        with open(cache_file, 'rb') as f:
            return f.read()
    
    # 如果没有缓存，生成新的
    response = requests.post('http://localhost:5001/v1/audio/speech', json={
        'input': text,
        'model': 'DeepSeek',
    })
    
    if response.status_code == 200:
        # 保存到缓存
        with open(cache_file, 'wb') as f:
            f.write(response.content)
        return response.content
    
    return None
```

### 2. 性能监测

```python
import requests
import time

def generate_with_timing(text: str):
    """记录生成时间"""
    
    start = time.time()
    
    response = requests.post('http://localhost:5001/v1/audio/speech', json={
        'input': text,
        'model': 'DeepSeek',
    })
    
    elapsed = time.time() - start
    
    if response.status_code == 200:
        size_kb = len(response.content) / 1024
        print(f"✓ 生成耗时: {elapsed:.2f}秒")
        print(f"✓ 文件大小: {size_kb:.1f}KB")
        print(f"✓ 速率: {size_kb/elapsed:.1f}KB/s")
        
        return response.content
    
    return None
```

### 3. 并发处理

```python
import requests
import concurrent.futures

def generate_batch_concurrent(texts: list, max_workers=3):
    """并发生成多个音频"""
    
    def generate_one(text):
        response = requests.post('http://localhost:5001/v1/audio/speech', json={
            'input': text,
            'model': 'DeepSeek',
        })
        return response.content if response.status_code == 200 else None
    
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(generate_one, text): text for text in texts}
        
        for future in concurrent.futures.as_completed(futures):
            text = futures[future]
            try:
                result = future.result()
                if result:
                    results.append({'text': text, 'audio': result})
            except Exception as e:
                print(f"✗ 生成失败: {e}")
    
    return results
```

---

**最后更新**: 2025年12月15日  
**版本**: 1.0  
**难度等级**: 初级 ~ 高级
