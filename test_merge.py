#!/usr/bin/env python3
"""
测试 PR #7 和 PR #10 合并后的功能
"""
import sys

def test_imports():
    """测试模块导入"""
    print("测试1: 导入模块...")
    try:
        from backend.app import app
        from backend.nano_tts import NanoAITTS
        from backend.tts_providers.nanoai import NanoAIProvider
        print("✓ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        return False


def test_nano_tts_methods():
    """测试 NanoAITTS 新方法"""
    print("\n测试2: 检查 NanoAITTS 新方法...")
    try:
        from backend.nano_tts import NanoAITTS
        engine = NanoAITTS()
        
        # 检查长文本处理相关方法
        assert hasattr(engine, 'split_text'), "缺少 split_text 方法"
        assert hasattr(engine, 'merge_audio_files'), "缺少 merge_audio_files 方法"
        assert hasattr(engine, 'process_long_text'), "缺少 process_long_text 方法"
        
        # 测试文本分割
        text = "这是一段测试文本。" * 100  # 约 1000 字符
        chunks = engine.split_text(text, max_chars=500)
        assert len(chunks) > 1, "长文本应该被分割"
        assert all(len(chunk) <= 500 for chunk in chunks), "分割后的片段应该 <= 500 字符"
        
        print(f"✓ 文本分割测试通过（{len(text)} 字符 -> {len(chunks)} 个片段）")
        
        # 测试 get_audio 方法签名
        import inspect
        sig = inspect.signature(engine.get_audio)
        params = list(sig.parameters.keys())
        expected_params = ['text', 'voice', 'speed', 'pitch', 'volume', 'language', 'gender', 'timeout', 'retry_count']
        for param in expected_params:
            assert param in params, f"get_audio 缺少参数: {param}"
        
        print("✓ get_audio 方法签名正确")
        return True
    except Exception as e:
        print(f"✗ NanoAITTS 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_app_endpoints():
    """测试 Flask 应用端点"""
    print("\n测试3: 检查 Flask 应用端点...")
    try:
        from backend.app import app
        
        # 检查所有路由
        routes = {}
        for rule in app.url_map.iter_rules():
            routes[rule.rule] = [method for method in rule.methods if method not in ['HEAD', 'OPTIONS']]
        
        # 检查必需的端点
        required_endpoints = [
            '/',
            '/v1/models',
            '/v1/audio/speech',
            '/v1/audio/diagnose',
            '/v1/providers',
            '/v1/config',
            '/v1/ui/config',
            '/v1/ui/config/secure',
            '/health',
        ]
        
        for endpoint in required_endpoints:
            if endpoint not in routes:
                print(f"✗ 缺少端点: {endpoint}")
                return False
        
        print(f"✓ 所有必需端点已定义（共 {len(routes)} 个端点）")
        
        # 检查 UI 配置端点方法
        assert 'GET' in routes['/v1/ui/config'], "/v1/ui/config 应该支持 GET"
        assert 'GET' in routes['/v1/ui/config/secure'], "/v1/ui/config/secure 应该支持 GET"
        assert 'PUT' in routes['/v1/ui/config/secure'], "/v1/ui/config/secure 应该支持 PUT"
        
        print("✓ UI 配置端点方法正确")
        return True
    except Exception as e:
        print(f"✗ Flask 应用测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_config_functions():
    """测试 UI 配置加密/解密功能"""
    print("\n测试4: 测试 UI 配置加密/解密...")
    try:
        from backend.app import encrypt_ui_config, decrypt_ui_config
        
        # 测试配置
        test_config = {
            "apiKey": "test-key-123",
            "baseUrl": "https://example.com",
            "provider": "nanoai",
            "settings": {
                "speed": 1.2,
                "pitch": 0.9,
            }
        }
        
        # 加密
        encrypted = encrypt_ui_config(test_config)
        assert 'v' in encrypted, "加密结果应该包含版本号"
        assert 'alg' in encrypted, "加密结果应该包含算法标识"
        assert 'mac' in encrypted, "加密结果应该包含 MAC"
        assert 'data' in encrypted, "加密结果应该包含加密数据"
        
        print("✓ 配置加密成功")
        
        # 解密
        decrypted = decrypt_ui_config(encrypted)
        assert decrypted == test_config, "解密后的配置应该与原始配置相同"
        
        print("✓ 配置解密成功")
        return True
    except Exception as e:
        print(f"✗ UI 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_provider_params():
    """测试 NanoAI provider 参数传递"""
    print("\n测试5: 测试 Provider 参数传递...")
    try:
        from backend.tts_providers.nanoai import NanoAIProvider
        import inspect
        
        provider = NanoAIProvider()
        
        # 检查 generate_audio 方法签名
        sig = inspect.signature(provider.generate_audio)
        params = list(sig.parameters.keys())
        assert 'text' in params, "generate_audio 应该有 text 参数"
        assert 'model' in params, "generate_audio 应该有 model 参数"
        assert 'options' in params, "generate_audio 应该有 options 参数"
        
        print("✓ Provider 方法签名正确")
        return True
    except Exception as e:
        print(f"✗ Provider 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("PR #7 和 PR #10 合并功能测试")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_nano_tts_methods,
        test_app_endpoints,
        test_ui_config_functions,
        test_provider_params,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"测试结果: {sum(results)}/{len(results)} 通过")
    print("=" * 60)
    
    if all(results):
        print("\n✓ 所有测试通过！PR #7 和 PR #10 功能已成功合并。")
        return 0
    else:
        print("\n✗ 部分测试失败，请检查上面的错误信息。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
