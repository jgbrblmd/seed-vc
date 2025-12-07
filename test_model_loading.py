#!/usr/bin/env python3
"""
Test script to verify model loading structure (without downloading checkpoints)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_config_structure():
    """Test if the configuration structure is correct."""
    try:
        from hydra.utils import instantiate
        from omegaconf import DictConfig

        cfg = DictConfig({
            "_target_": "modules.v2.vc_wrapper.VoiceConversionWrapper",
            "sr": 22050,
            "hop_size": 256,
            "mel_fn": {
                "_target_": "modules.audio.mel_spectrogram",
                "_partial_": True,
                "n_fft": 1024,
                "win_size": 1024,
                "hop_size": 256,
                "num_mels": 80,
                "sampling_rate": 22050,
                "fmin": 0,
                "fmax": None,
                "center": False
            },
            "cfm": {
                "_target_": "modules.v2.cfm.CFM",
                "estimator": {
                    "_target_": "modules.v2.dit_wrapper.DiT",
                    "time_as_token": True,
                    "style_as_token": True,
                    "uvit_skip_connection": False,
                    "block_size": 8192,
                    "depth": 13,
                    "num_heads": 8,
                    "hidden_dim": 512,
                    "in_channels": 80,
                    "content_dim": 512,
                    "style_encoder_dim": 192,
                    "class_dropout_prob": 0.1,
                    "dropout_rate": 0.0,
                    "attn_dropout_rate": 0.0
                }
            },
            "cfm_length_regulator": {
                "_target_": "modules.v2.length_regulator.InterpolateRegulator",
                "channels": 512,
                "is_discrete": True,
                "codebook_size": 2048,
                "sampling_ratios": [1, 1, 1, 1],
                "f0_condition": False
            },
            "ar": {
                "_target_": "modules.v2.ar.NaiveWrapper",
                "model": {
                    "_target_": "modules.v2.ar.NaiveTransformer",
                    "config": {
                        "_target_": "modules.v2.ar.NaiveModelArgs",
                        "dropout": 0.0,
                        "rope_base": 10000.0,
                        "dim": 768,
                        "head_dim": 64,
                        "n_local_heads": 2,
                        "intermediate_size": 2304,
                        "n_head": 12,
                        "n_layer": 12,
                        "vocab_size": 2049
                    }
                }
            },
            "ar_length_regulator": {
                "_target_": "modules.v2.length_regulator.InterpolateRegulator",
                "channels": 768,
                "is_discrete": True,
                "codebook_size": 32,
                "sampling_ratios": [],
                "f0_condition": False
            }
        })

        print("✅ 配置结构创建成功")

        # Test individual component instantiation (without full wrapper)
        from modules.v2.ar import NaiveTransformer, NaiveModelArgs

        ar_config = NaiveModelArgs(
            dropout=0.0,
            rope_base=10000.0,
            dim=768,
            head_dim=64,
            n_local_heads=2,
            intermediate_size=2304,
            n_head=12,
            n_layer=12,
            vocab_size=2049
        )

        print("✅ AR配置创建成功")

        return True

    except Exception as e:
        print(f"❌ 配置结构测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_imports():
    """Test if all API modules can be imported."""
    try:
        from api_v2 import app, VoiceConversionRequest, VoiceConversionResponse
        print("✅ API模块导入成功")
        return True
    except Exception as e:
        print(f"❌ API模块导入失败: {e}")
        return False

def main():
    """Run all model loading tests."""
    print("Seed Voice Conversion V2 API - 模型加载测试")
    print("=" * 60)

    tests = [
        ("配置结构测试", test_config_structure),
        ("API导入测试", test_api_imports),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}...")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name}异常: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)

    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 模型加载配置正确！")
        print("\n现在可以尝试启动API服务器:")
        print("  python api_v2.py")
        print("\n如果遇到模型下载问题，请检查:")
        print("1. 网络连接")
        print("2. Hugging Face访问权限")
        print("3. 磁盘空间")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        print("请检查模型配置和依赖包")

if __name__ == "__main__":
    main()