#!/usr/bin/env python3
"""
测试修复后的API认证调试功能
"""

import requests
import json
import os

def test_auth_debug_endpoint():
    """测试认证调试端点"""
    print("🔍 测试认证调试端点...")
    base_url = "http://localhost:5001"
    
    try:
        response = requests.get(f"{base_url}/v1/config/auth-debug", timeout=10)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"调试端点测试失败: {e}")
        return False

def test_config_endpoint():
    """测试配置端点"""
    print("🔧 测试配置端点...")
    base_url = "http://localhost:5001"
    
    try:
        response = requests.get(f"{base_url}/v1/config", timeout=10)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"配置端点测试失败: {e}")
        return False

def test_invalid_auth():
    """测试无效认证（应该返回401和详细错误）"""
    print("❌ 测试无效认证...")
    base_url = "http://localhost:5001"
    
    test_key = "sk-test-invalid-key-27-chars-long"
    headers = {"Authorization": f"Bearer {test_key}"}
    data = {"model": "DeepSeek", "input": "测试文本"}
    
    try:
        response = requests.post(f"{base_url}/v1/audio/speech", headers=headers, json=data, timeout=10)
        print(f"状态码: {response.status_code}")
        if response.status_code == 401:
            print("✅ 正确返回401错误")
            print(f"错误响应: {response.json()}")
            return True
        else:
            print(f"❌ 预期401，但实际收到{response.status_code}")
            print(f"响应: {response.text}")
            return False
    except Exception as e:
        print(f"无效认证测试失败: {e}")
        return False

def test_valid_auth():
    """测试有效认证"""
    print("✅ 测试有效认证...")
    base_url = "http://localhost:5001"
    
    # 使用当前环境中的API Key
    api_key = os.getenv('SERVICE_API_KEY') or os.getenv('TTS_API_KEY') or "sk-nanoai-your-secret-key"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"model": "DeepSeek", "input": "测试文本"}
    
    try:
        response = requests.post(f"{base_url}/v1/audio/speech", headers=headers, json=data, timeout=30)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 认证成功")
            print(f"音频大小: {len(response.content)} 字节")
            return True
        else:
            print(f"❌ 认证失败")
            print(f"错误响应: {response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text}")
            return False
    except Exception as e:
        print(f"有效认证测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🔧 API认证调试功能测试")
    print("=" * 60)
    
    base_url = "http://localhost:5001"
    api_key = os.getenv('SERVICE_API_KEY') or os.getenv('TTS_API_KEY') or "sk-nanoai-your-secret-key"
    
    print(f"测试配置:")
    print(f"  基础URL: {base_url}")
    print(f"  当前API Key: ***{api_key[-4:]} (长度: {len(api_key)})")
    print()
    
    # 运行测试
    tests = [
        ("认证调试端点", test_auth_debug_endpoint),
        ("配置端点", test_config_endpoint), 
        ("无效认证", test_invalid_auth),
        ("有效认证", test_valid_auth),
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
        print("🎉 所有测试通过！认证调试功能正常")
    elif passed >= total * 0.75:
        print("⚠️  大部分测试通过，主要功能正常")
    else:
        print("❌ 多数测试失败，需要进一步调试")

if __name__ == "__main__":
    main()