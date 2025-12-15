#!/usr/bin/env python3
"""
诊断脚本：测试 TTS 服务的bot.n.cn API连接
"""

import sys
import json
import os
import requests
import time
from urllib.parse import quote

def test_diagnosis_endpoint():
    """测试诊断端点"""
    print("🔍 测试诊断端点...")
    base_url = "http://localhost:5001"
    try:
        response = requests.get(f"{base_url}/v1/audio/diagnose", timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"诊断端点测试失败: {e}")
        return False

def test_health_endpoint():
    """测试健康检查端点"""
    print("🏥 测试健康检查端点...")
    base_url = "http://localhost:5001"
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查端点测试失败: {e}")
        return False

def test_models_endpoint():
    """测试模型列表端点"""
    print("🤖 测试模型列表端点...")
    base_url = "http://localhost:5001"
    api_key = "sk-nanoai-your-secret-key"
    
    if os.getenv('TTS_API_KEY'):
        api_key = os.getenv('TTS_API_KEY')
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{base_url}/v1/models", headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        data = response.json()
        if response.status_code == 200:
            models = data.get("data", [])
            print(f"可用模型数量: {len(models)}")
            for model in models[:3]:  # 显示前3个模型
                print(f"  - {model.get('id')}: {model.get('description', 'No description')}")
        else:
            print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"模型列表端点测试失败: {e}")
        return False

def test_tts_endpoint():
    """测试TTS端点"""
    print("🎵 测试TTS端点...")
    base_url = "http://localhost:5001"
    api_key = "sk-nanoai-your-secret-key"
    
    if os.getenv('TTS_API_KEY'):
        api_key = os.getenv('TTS_API_KEY')
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "DeepSeek",
            "input": "测试文本，验证TTS功能是否正常工作"
        }
        
        start_time = time.time()
        response = requests.post(f"{base_url}/v1/audio/speech", headers=headers, json=data, timeout=60)
        duration = time.time() - start_time
        
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {duration:.2f}秒")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', 'unknown')
            content_length = len(response.content)
            first_16_bytes = response.content[:16].hex()
            
            print(f"内容类型: {content_type}")
            print(f"音频大小: {content_length} 字节")
            print(f"前16字节: {first_16_bytes}")
            
            # 检查是否是MP3文件头
            if response.content.startswith(b'ID3') or (response.content[0] == 0xFF and (response.content[1] & 0xE0) == 0xE0):
                print("✅ 音频格式验证通过")
            else:
                print("❌ 音频格式验证失败")
                print(f"响应内容预览: {response.content[:100]}")
            
            return True
        else:
            error_data = response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text
            print(f"错误响应: {json.dumps(error_data, ensure_ascii=False, indent=2) if isinstance(error_data, dict) else error_data}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ TTS请求超时")
        return False
    except Exception as e:
        print(f"❌ TTS端点测试失败: {e}")
        return False

def test_environment_check():
    """检查环境配置"""
    print("🔧 检查环境配置...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        config = {
            "API_KEY": "***" if os.getenv('TTS_API_KEY') and os.getenv('TTS_API_KEY') != 'sk-nanoai-your-secret-key' else "not_configured",
            "HTTP_TIMEOUT": os.getenv('HTTP_TIMEOUT', '30'),
            "RETRY_COUNT": os.getenv('RETRY_COUNT', '2'),
            "PROXY_URL": os.getenv('PROXY_URL', 'none'),
            "SSL_VERIFY": os.getenv('SSL_VERIFY', 'true'),
            "CACHE_DIR": os.getenv('CACHE_DIR', 'cache'),
            "DEBUG": os.getenv('DEBUG', 'False')
        }
        
        print("环境配置:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        return True
    except Exception as e:
        print(f"环境检查失败: {e}")
        return False

def main():
    """主测试函数"""
    import os
    print("=" * 60)
    print("🔍 TTS Bot.n.cn API 连接诊断测试")
    print("=" * 60)
    
    base_url = "http://localhost:5001"
    api_key = "sk-nanoai-your-secret-key"
    
    # 检查环境变量
    if os.getenv('TTS_API_KEY'):
        api_key = os.getenv('TTS_API_KEY')
    
    print(f"测试配置:")
    print(f"  基础URL: {base_url}")
    print(f"  API密钥: {'***' + api_key[-4:] if len(api_key) > 8 else '***'}")
    print()
    
    # 运行测试
    tests = [
        ("环境检查", test_environment_check),
        ("健康检查", test_health_endpoint),
        ("诊断端点", test_diagnosis_endpoint),
        ("模型列表", test_models_endpoint),
        ("TTS功能", test_tts_endpoint),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 {test_name}测试")
        print(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
        except Exception as e:
            results.append((test_name, False))
            print(f"{test_name}: ❌ 异常 - {e}")
        
        time.sleep(1)  # 短暂等待
    
    # 汇总结果
    print(f"\n{'='*60}")
    print("📊 测试结果汇总")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！TTS服务正常工作")
    elif passed >= total * 0.6:
        print("⚠️  部分测试通过，服务基本可用")
    else:
        print("❌ 多数测试失败，需要检查配置")

if __name__ == "__main__":
    main()