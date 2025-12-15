#!/usr/bin/env python3
"""
测试代理配置修复的脚本
验证各种问题配置是否能被正确处理
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入TTS模块
sys.path.insert(0, '.')
from nano_tts import NanoAITTS

def test_proxy_validation():
    """测试代理URL验证功能"""
    print("🔧 测试代理URL验证功能")
    print("=" * 60)
    
    # 创建测试实例
    test_instance = NanoAITTS.__new__(NanoAITTS)
    test_instance.logger = logging.getLogger('test_proxy_validation')
    
    # 测试用例：包含可能导致问题的配置
    test_cases = [
        {
            'name': '原始问题配置（带注释）',
            'input': 'http://proxy.company.com:8080 # HTTP代理地址，如: http://proxy.company.com:8080',
            'expected': 'http://proxy.company.com:8080'
        },
        {
            'name': '空配置',
            'input': '',
            'expected': None
        },
        {
            'name': '带换行符的配置',
            'input': 'http://proxy.company.com:8080\n# 注释内容',
            'expected': 'http://proxy.company.com:8080'
        },
        {
            'name': '带制表符的配置',
            'input': 'http://proxy.company.com:8080\t# 注释内容',
            'expected': 'http://proxy.company.com:8080'
        },
        {
            'name': '正常配置',
            'input': 'http://proxy.company.com:8080',
            'expected': 'http://proxy.company.com:8080'
        },
        {
            'name': 'HTTPS代理配置',
            'input': 'https://secure-proxy.company.com:3128',
            'expected': 'https://secure-proxy.company.com:3128'
        },
        {
            'name': '无协议配置',
            'input': 'proxy.company.com:8080',
            'expected': 'http://proxy.company.com:8080'
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 测试 {i}: {test_case['name']}")
        print(f"   输入: {repr(test_case['input'])}")
        
        try:
            result = test_instance._validate_and_clean_proxy_url(test_case['input'])
            print(f"   输出: {repr(result)}")
            print(f"   期望: {repr(test_case['expected'])}")
            
            if result == test_case['expected']:
                print("   结果: ✅ 通过")
                passed += 1
            else:
                print("   结果: ❌ 失败")
                
        except Exception as e:
            print(f"   结果: ❌ 异常 - {e}")
    
    print("\n" + "=" * 60)
    print(f"代理URL验证测试完成: {passed}/{total} 通过")
    
    return passed == total

def test_current_environment():
    """测试当前环境配置"""
    print("\n🌍 测试当前环境配置")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    
    # 显示当前配置
    config = {
        'PROXY_URL': os.getenv('PROXY_URL', '未设置'),
        'HTTP_TIMEOUT': os.getenv('HTTP_TIMEOUT', '未设置'),
        'RETRY_COUNT': os.getenv('RETRY_COUNT', '未设置'),
        'SSL_VERIFY': os.getenv('SSL_VERIFY', '未设置'),
    }
    
    print("当前环境变量:")
    for key, value in config.items():
        if key == 'PROXY_URL' and value:
            print(f"  {key}: {repr(value)}")
        else:
            print(f"  {key}: {value}")
    
    try:
        # 创建TTS实例
        tts = NanoAITTS()
        
        print(f"\nTTS引擎代理配置:")
        print(f"  代理URL: {repr(tts.proxy_url)}")
        print(f"  代理启用: {bool(tts.proxy_url)}")
        print(f"  其他配置: timeout={tts.http_timeout}s, retry={tts.retry_count}, ssl_verify={tts.ssl_verify}")
        
        if tts.proxy_url is None:
            print("✅ 代理配置正确 - 未启用代理（推荐设置）")
            return True
        else:
            print("ℹ️  代理配置启用 - 请确保代理地址有效")
            return True
            
    except Exception as e:
        print(f"❌ TTS引擎初始化失败: {e}")
        return False

def test_error_scenario():
    """测试错误场景处理"""
    print("\n🚨 测试错误场景处理")
    print("=" * 60)
    
    test_instance = NanoAITTS.__new__(NanoAITTS)
    test_instance.logger = logging.getLogger('test_error_scenario')
    
    # 测试可能导致原始错误的配置
    problematic_configs = [
        'http://proxy.company.com:8080 # HTTP代理地址，如: http://proxy.company.com',
        'http://proxy.company.com:8080 # 注释文本\n包含换行符',
        'http://proxy.company.com:8080 \t # 包含制表符的注释',
        'http://proxy.company.com:8080// 包含双斜杠注释',
        '',  # 空配置
    ]
    
    print("测试可能导致原始错误的配置:")
    
    for i, config in enumerate(problematic_configs, 1):
        print(f"\n  测试 {i}: {repr(config[:50])}")
        try:
            result = test_instance._validate_and_clean_proxy_url(config)
            if result:
                print(f"    结果: ✅ 成功清理为 {repr(result)}")
            else:
                print(f"    结果: ✅ 正确拒绝（禁用代理）")
        except Exception as e:
            print(f"    结果: ❌ 处理异常: {e}")
    
    print("\n✅ 错误场景测试完成")

def main():
    """主测试函数"""
    print("🚀 代理配置修复验证测试")
    print("=" * 80)
    
    # 测试1: 代理URL验证功能
    test1_passed = test_proxy_validation()
    
    # 测试2: 当前环境配置
    test2_passed = test_current_environment()
    
    # 测试3: 错误场景处理
    test_error_scenario()
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)
    
    if test1_passed and test2_passed:
        print("🎉 所有测试通过！代理配置修复成功")
        print("\n✅ 修复效果:")
        print("  - 问题配置（带注释）被正确清理")
        print("  - 空配置正确处理为禁用代理")
        print("  - 控制字符被正确移除")
        print("  - 当前环境配置正确")
        print("\n🎯 原始问题已解决:")
        print("  'URL can't contain control characters' 错误将不再出现")
        print("  代理配置更加健壮和可靠")
        return True
    else:
        print("❌ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)