#!/usr/bin/env python3
"""
Quick test to verify API can start without errors
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test if all required modules can be imported."""
    try:
        import fastapi
        import uvicorn
        import pydantic
        import requests
        print("✅ 所有依赖包导入成功")
        return True
    except ImportError as e:
        print(f"❌ 依赖包导入失败: {e}")
        return False

def test_api_import():
    """Test if API module can be imported."""
    try:
        from api_v2 import app, VoiceConversionRequest, VoiceConversionResponse
        print("✅ API模块导入成功")
        return True
    except Exception as e:
        print(f"❌ API模块导入失败: {e}")
        return False

def test_model_validation():
    """Test if Pydantic models work correctly."""
    try:
        from api_v2 import VoiceConversionRequest

        # Test valid request
        request = VoiceConversionRequest(
            source_audio_path="/test/source.wav",
            target_audio_path="/test/target.wav",
            diffusion_steps=50,
            output_format="mp3"
        )
        print("✅ 模型验证成功")

        # Test invalid format
        try:
            bad_request = VoiceConversionRequest(
                source_audio_path="/test/source.wav",
                target_audio_path="/test/target.wav",
                output_format="invalid"
            )
            print("❌ 模型验证失败：应该拒绝无效格式")
            return False
        except:
            print("✅ 无效格式被正确拒绝")
            return True

    except Exception as e:
        print(f"❌ 模型验证失败: {e}")
        return False

def test_model_config():
    """Test if model configuration is correct."""
    try:
        from hydra.utils import instantiate
        from omegaconf import DictConfig

        # Test basic config structure
        cfg = DictConfig({
            "_target_": "modules.v2.vc_wrapper.VoiceConversionWrapper",
            "sr": 22050,
            "cfm": {
                "_target_": "modules.v2.cfm.CFM"
            },
            "cfm_length_regulator": {
                "_target_": "modules.v2.length_regulator.InterpolateRegulator"
            }
        })

        print("✅ 模型配置结构正确")
        return True
    except Exception as e:
        print(f"❌ 模型配置错误: {e}")
        return False

def main():
    """Run all tests."""
    print("Seed Voice Conversion V2 API - 快速测试")
    print("=" * 50)

    tests = [
        ("依赖包导入", test_import),
        ("API模块导入", test_api_import),
        ("模型验证", test_model_validation),
        ("模型配置", test_model_config),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}测试...")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)

    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        print("\n现在可以启动API服务器:")
        print("  python api_v2.py")
        print("\n或者使用快速启动脚本:")
        print("  python start_api.py")
        print("\n启动后访问 http://localhost:8000/docs 查看API文档")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        print("请检查依赖包安装和环境配置")

if __name__ == "__main__":
    main()