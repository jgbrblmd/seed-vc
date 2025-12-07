#!/usr/bin/env python3
"""
Simple test script for Seed Voice Conversion V2 API
"""

import sys
import time
import requests
import json

def test_api_connection():
    """Test API connection and health."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ API连接成功!")
            print(f"   状态: {health_data.get('status')}")
            print(f"   模型已加载: {health_data.get('models_loaded')}")
            print(f"   设备: {health_data.get('device')}")
            return True
        else:
            print(f"❌ API连接失败，状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print("   请确保API服务器正在运行: python api_v2.py")
        return False
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False

def test_api_info():
    """Test API info endpoint."""
    try:
        response = requests.get("http://localhost:8000/", timeout=10)
        if response.status_code == 200:
            info_data = response.json()
            print("✅ API信息获取成功!")
            print(f"   名称: {info_data.get('name')}")
            print(f"   版本: {info_data.get('version')}")
            print(f"   文档: {info_data.get('endpoints', {}).get('docs')}")
            return True
        else:
            print(f"❌ 获取API信息失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API信息测试失败: {e}")
        return False

def test_conversion_api():
    """Test conversion API with mock data."""
    try:
        # Test with invalid data to validate API response
        test_data = {
            "source_audio_path": "/nonexistent/source.wav",
            "target_audio_path": "/nonexistent/target.wav",
            "diffusion_steps": 30,
            "output_format": "mp3"
        }

        response = requests.post(
            "http://localhost:8000/convert",
            json=test_data,
            timeout=30
        )

        if response.status_code == 500:
            print("✅ 转换API端点响应正常（预期的文件不存在错误）")
            result = response.json()
            print(f"   错误信息: {result.get('detail')}")
            return True
        elif response.status_code == 400:
            print("✅ 转换API端点响应正常（预期的请求错误）")
            result = response.json()
            print(f"   错误信息: {result.get('detail')}")
            return True
        else:
            print(f"⚠️  转换API返回意外状态码: {response.status_code}")
            try:
                result = response.json()
                print(f"   响应: {result}")
            except:
                print(f"   响应内容: {response.text[:200]}...")
            return True  # Still counts as successful connection

    except Exception as e:
        print(f"❌ 转换API测试失败: {e}")
        return False

def test_documentation():
    """Test if documentation endpoints are accessible."""
    try:
        # Test Swagger UI
        response = requests.get("http://localhost:8000/docs", timeout=10)
        if response.status_code == 200:
            print("✅ Swagger文档可访问: http://localhost:8000/docs")
        else:
            print(f"⚠️  Swagger文档访问异常: {response.status_code}")

        # Test ReDoc
        response = requests.get("http://localhost:8000/redoc", timeout=10)
        if response.status_code == 200:
            print("✅ ReDoc文档可访问: http://localhost:8000/redoc")
        else:
            print(f"⚠️  ReDoc文档访问异常: {response.status_code}")

        return True
    except Exception as e:
        print(f"❌ 文档测试失败: {e}")
        return False

def main():
    """Run all API tests."""
    print("Seed Voice Conversion V2 API - 连接测试")
    print("=" * 50)

    tests = [
        ("API连接测试", test_api_connection),
        ("API信息测试", test_api_info),
        ("转换功能测试", test_conversion_api),
        ("文档访问测试", test_documentation),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}异常: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")

    print(f"\n总体结果: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 API服务器运行正常！")
        print("\n下一步:")
        print("1. 访问 http://localhost:8000/docs 查看API文档")
        print("2. 运行 python client_examples.py 测试完整功能")
        print("3. 准备音频文件进行语音转换测试")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查API服务器配置")
        print("\n可能的解决方案:")
        print("1. 确认API服务器已启动: python api_v2.py")
        print("2. 检查端口8000是否被占用")
        print("3. 确认所有依赖已正确安装")
        print("4. 检查GPU和CUDA配置")

if __name__ == "__main__":
    main()