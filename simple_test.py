#!/usr/bin/env python3
"""
简单测试：验证API认证调试功能
"""

import json
import requests
import time

def test_debug_endpoint():
    """测试认证调试端点"""
    try:
        response = requests.get("http://localhost:5001/v1/config/auth-debug", timeout=10)
        print(f"调试端点状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ 调试端点正常")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ 调试端点错误: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"调试端点测试失败: {e}")
        return False

def test_invalid_auth():
    """测试无效认证（27字符key，应返回401和详细错误）"""
    try:
        test_key = "sk-test-invalid-key-27-chars"  # 27字符
        headers = {"Authorization": f"Bearer {test_key}"}
        data = {"model": "DeepSeek", "input": "测试"}
        
        response = requests.post("http://localhost:5001/v1/audio/speech", 
                               headers=headers, json=data, timeout=10)
        print(f"认证测试状态码: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ 正确返回401错误")
            try:
                error_data = response.json()
                print(f"错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误响应: {response.text}")
            return True
        else:
            print(f"❌ 预期401，但收到: {response.status_code}")
            print(f"响应: {response.text}")
            return False
    except Exception as e:
        print(f"认证测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🔍 测试API认证调试功能")
    print("="*50)
    
    time.sleep(2)  # 等待服务器完全启动
    
    # 测试调试端点
    debug_result = test_debug_endpoint()
    
    print("\n" + "="*50)
    
    # 测试认证（应该失败并显示详细错误）
    auth_result = test_invalid_auth()
    
    print("\n" + "="*50)
    print("📊 测试结果:")
    print(f"调试端点: {'✅ 通过' if debug_result else '❌ 失败'}")
    print(f"认证测试: {'✅ 通过' if auth_result else '❌ 失败'}")
    
    if debug_result and auth_result:
        print("\n🎉 测试通过！认证调试功能正常工作")
    else:
        print("\n❌ 测试失败，需要进一步检查")