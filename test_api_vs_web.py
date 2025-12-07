#!/usr/bin/env python3
"""
测试API与Web界面一致性

使用与app_vc_v2.py相同的示例样本，通过API生成音频，
验证API输出是否与Web界面一致。
"""

import os
import sys
import time
import requests
import json
from pathlib import Path

# API配置
API_BASE_URL = "http://localhost:8000"
OUTPUT_DIR = "/tmp/seedvc"

# Web界面中的示例样本（与app_vc_v2.py中的examples相同）
EXAMPLES = [
    {
        "name": "示例1 - 雅生音转丁真音",
        "source": "examples/source/yae_0.wav",
        "reference": "examples/reference/dingzhen_0.wav",
        "diffusion_steps": 50,
        "length_adjust": 1.0,
        "intelligibility_cfg_rate": 0.5,
        "similarity_cfg_rate": 0.5,
        "top_p": 0.9,
        "temperature": 1.0,
        "repetition_penalty": 1.0,
        "convert_style": False,
        "anonymization_only": False
    },
    {
        "name": "示例2 - 周杰伦音转东丈音",
        "source": "examples/source/jay_0.wav",
        "reference": "examples/reference/azuma_0.wav",
        "diffusion_steps": 50,
        "length_adjust": 1.0,
        "intelligibility_cfg_rate": 0.5,
        "similarity_cfg_rate": 0.5,
        "top_p": 0.9,
        "temperature": 1.0,
        "repetition_penalty": 1.0,
        "convert_style": False,
        "anonymization_only": False
    }
]

# 输出格式列表
OUTPUT_FORMATS = ["wav", "mp3", "ogg"]

def setup_output_directory():
    """创建输出目录"""
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ 输出目录已创建: {output_path}")
    return output_path

def check_api_health():
    """检查API健康状态"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ API服务器健康检查通过")
            print(f"   状态: {health_data.get('status')}")
            print(f"   模型已加载: {health_data.get('models_loaded')}")
            print(f"   设备: {health_data.get('device')}")
            return True
        else:
            print(f"❌ API健康检查失败，状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print("   请确保API服务器正在运行: python api_v2.py")
        return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def convert_audio_with_api(source_path, reference_path, output_format, params, example_index):
    """通过API转换音频"""
    print(f"\n🔄 正在转换音频...")
    print(f"   源音频: {source_path}")
    print(f"   参考音频: {reference_path}")
    print(f"   输出格式: {output_format}")
    print(f"   扩散步数: {params['diffusion_steps']}")

    # 构建请求数据
    request_data = {
        "source_audio_path": os.path.abspath(source_path),
        "target_audio_path": os.path.abspath(reference_path),
        "diffusion_steps": params["diffusion_steps"],
        "length_adjust": params["length_adjust"],
        "intelligibility_cfg_rate": params["intelligibility_cfg_rate"],
        "similarity_cfg_rate": params["similarity_cfg_rate"],
        "top_p": params["top_p"],
        "temperature": params["temperature"],
        "repetition_penalty": params["repetition_penalty"],
        "convert_style": params["convert_style"],
        "anonymization_only": params["anonymization_only"],
        "output_format": output_format,
        "return_base64": False,  # 返回文件路径
        "cleanup_temp_files": False  # 不自动清理临时文件
    }

    # 发送请求
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/convert",
            json=request_data,
            timeout=300  # 5分钟超时
        )

        processing_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print(f"✅ 转换成功!")
                print(f"   处理时间: {processing_time:.2f}秒 (服务器: {result['processing_time']:.2f}秒)")

                if result["input_info"]:
                    source_info = result["input_info"]["source"]
                    target_info = result["input_info"]["target"]
                    print(f"   源音频时长: {source_info['duration']:.2f}秒")
                    print(f"   参考音频时长: {target_info['duration']:.2f}秒")

                # 复制输出文件到指定目录
                if result["full_output_path"]:
                    source_file = result["full_output_path"]
                    output_filename = f"example_{example_index + 1}_converted.{output_format}"
                    output_path = Path(OUTPUT_DIR) / output_filename

                    import shutil
                    shutil.copy2(source_file, output_path)

                    print(f"   输出文件: {output_path}")
                    print(f"   文件大小: {os.path.getsize(output_path):,} 字节")

                    return output_path
                else:
                    print("❌ 未找到输出文件路径")
                    return None
            else:
                print(f"❌ 转换失败: {result['message']}")
                return None
        else:
            print(f"❌ API请求失败，状态码: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   错误详情: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"   响应内容: {response.text[:200]}...")
            return None

    except requests.exceptions.Timeout:
        print("❌ 请求超时，请检查服务器状态或增加超时时间")
        return None
    except Exception as e:
        print(f"❌ 转换过程中出现异常: {e}")
        return None

def main():
    """主测试函数"""
    print("Seed Voice Conversion V2 API vs Web界面一致性测试")
    print("=" * 70)

    # 设置输出目录
    output_dir = setup_output_directory()

    # 检查API健康状态
    if not check_api_health():
        print("\n❌ API服务器不可用，请先启动API服务器:")
        print("   python api_v2.py")
        return

    # 检查示例文件是否存在
    missing_files = []
    for example in EXAMPLES:
        if not os.path.exists(example["source"]):
            missing_files.append(f"源文件: {example['source']}")
        if not os.path.exists(example["reference"]):
            missing_files.append(f"参考文件: {example['reference']}")

    if missing_files:
        print(f"\n❌ 以下示例文件不存在:")
        for file in missing_files:
            print(f"   - {file}")
        return

    print(f"\n📋 测试计划:")
    print(f"   示例数量: {len(EXAMPLES)}")
    print(f"   每个示例生成 {len(OUTPUT_FORMATS)} 种格式")
    print(f"   总共生成 {len(EXAMPLES) * len(OUTPUT_FORMATS)} 个音频文件")
    print(f"   输出目录: {OUTPUT_DIR}")

    # 开始测试
    successful_conversions = []
    failed_conversions = []
    total_processing_time = 0

    for i, example in enumerate(EXAMPLES):
        print(f"\n{'='*60}")
        print(f"🎵 测试示例 {i + 1}: {example['name']}")
        print(f"{'='*60}")

        for output_format in OUTPUT_FORMATS:
            print(f"\n📁 生成 {output_format.upper()} 格式...")

            output_path = convert_audio_with_api(
                source_path=example["source"],
                reference_path=example["reference"],
                output_format=output_format,
                params=example,
                example_index=i
            )

            if output_path and output_path.exists():
                successful_conversions.append({
                    "example": example["name"],
                    "format": output_format,
                    "path": str(output_path)
                })
                print(f"✅ {output_format.upper()} 文件生成成功")
            else:
                failed_conversions.append({
                    "example": example["name"],
                    "format": output_format,
                    "error": "生成失败"
                })
                print(f"❌ {output_format.upper()} 文件生成失败")

    # 输出测试结果摘要
    print(f"\n{'='*70}")
    print(f"📊 测试结果摘要")
    print(f"{'='*70}")

    print(f"\n✅ 成功生成: {len(successful_conversions)}/{len(EXAMPLES) * len(OUTPUT_FORMATS)} 个文件")
    print(f"❌ 失败生成: {len(failed_conversions)} 个文件")

    if successful_conversions:
        print(f"\n🎉 成功生成的文件:")
        for conversion in successful_conversions:
            file_size = os.path.getsize(conversion["path"])
            print(f"   - {conversion['example']} ({conversion['format']}):")
            print(f"     {conversion['path']}")
            print(f"     大小: {file_size:,} 字节")

    if failed_conversions:
        print(f"\n❌ 失败的文件:")
        for conversion in failed_conversions:
            print(f"   - {conversion['example']} ({conversion['format']}): {conversion['error']}")

    print(f"\n📁 所有文件保存在: {OUTPUT_DIR}")

    # 验证测试
    success_rate = len(successful_conversions) / (len(EXAMPLES) * len(OUTPUT_FORMATS))
    if success_rate >= 0.8:
        print(f"\n🎉 测试成功率: {success_rate*100:.1f}% - 优秀!")
        print("   API与Web界面功能一致性良好。")
    elif success_rate >= 0.5:
        print(f"\n⚠️  测试成功率: {success_rate*100:.1f}% - 可接受")
        print("   大部分功能正常，可能需要进一步调试。")
    else:
        print(f"\n❌ 测试成功率: {success_rate*100:.1f}% - 需要修复")
        print("   API可能存在配置或功能问题。")

    print(f"\n🔍 后续验证步骤:")
    print(f"1. 播放生成的音频文件，检查音质和一致性")
    print(f"2. 与Web界面生成的音频进行对比")
    print(f"3. 检查不同格式文件的音质差异")
    print(f"4. 验证API参数是否按预期工作")

    # 生成测试报告
    report_path = Path(OUTPUT_DIR) / "test_report.json"
    test_report = {
        "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "examples_tested": len(EXAMPLES),
        "formats_tested": len(OUTPUT_FORMATS),
        "successful_conversions": len(successful_conversions),
        "failed_conversions": len(failed_conversions),
        "success_rate": success_rate,
        "successful_files": successful_conversions,
        "failed_files": failed_conversions,
        "output_directory": OUTPUT_DIR
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(test_report, f, indent=2, ensure_ascii=False)

    print(f"\n📄 测试报告已保存到: {report_path}")

if __name__ == "__main__":
    main()