#!/usr/bin/env python3
"""
Seed Voice Conversion V2 API - Client Examples

This file provides various examples of how to use the Seed Voice Conversion API.
"""

import requests
import base64
import json
import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional

class VoiceConversionClient:
    """Client for Seed Voice Conversion API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()

    def convert_with_files(
        self,
        source_path: str,
        target_path: str,
        diffusion_steps: int = 30,
        output_format: str = "wav",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convert voice using file paths.

        Args:
            source_path: Path to source audio file
            target_path: Path to reference audio file
            diffusion_steps: Number of diffusion steps
            output_format: Output format (wav/mp3/ogg)
            **kwargs: Additional parameters

        Returns:
            API response dictionary
        """
        data = {
            "source_audio_path": source_path,
            "target_audio_path": target_path,
            "diffusion_steps": diffusion_steps,
            "output_format": output_format,
            **kwargs
        }

        response = self.session.post(
            f"{self.base_url}/convert",
            json=data
        )
        return response.json()

    def convert_with_base64(
        self,
        source_path: str,
        target_path: str,
        diffusion_steps: int = 30,
        output_format: str = "wav",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convert voice using Base64 encoded audio.

        Args:
            source_path: Path to source audio file
            target_path: Path to reference audio file
            diffusion_steps: Number of diffusion steps
            output_format: Output format (wav/mp3/ogg)
            **kwargs: Additional parameters

        Returns:
            API response dictionary
        """
        # Encode files to base64
        source_base64 = self._file_to_base64(source_path)
        target_base64 = self._file_to_base64(target_path)

        data = {
            "source_audio_base64": source_base64,
            "target_audio_base64": target_base64,
            "diffusion_steps": diffusion_steps,
            "output_format": output_format,
            "return_base64": True,
            **kwargs
        }

        response = self.session.post(
            f"{self.base_url}/convert",
            json=data
        )
        return response.json()

    def convert_with_upload(
        self,
        source_path: str,
        target_path: str,
        diffusion_steps: int = 30,
        output_format: str = "wav",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convert voice by uploading files.

        Args:
            source_path: Path to source audio file
            target_path: Path to reference audio file
            diffusion_steps: Number of diffusion steps
            output_format: Output format (wav/mp3/ogg)
            **kwargs: Additional parameters

        Returns:
            API response dictionary
        """
        files = {
            'source_audio': open(source_path, 'rb'),
            'target_audio': open(target_path, 'rb')
        }

        data = {
            'diffusion_steps': diffusion_steps,
            'output_format': output_format,
            **kwargs
        }

        try:
            response = self.session.post(
                f"{self.base_url}/convert/files",
                files=files,
                data=data
            )
            return response.json()
        finally:
            files['source_audio'].close()
            files['target_audio'].close()

    def _file_to_base64(self, file_path: str) -> str:
        """Convert file to base64 string."""
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def save_base64_audio(self, base64_data: str, output_path: str):
        """Save base64 encoded audio to file."""
        audio_data = base64.b64decode(base64_data)
        with open(output_path, "wb") as f:
            f.write(audio_data)


def example_basic_conversion():
    """基本语音转换示例"""
    print("=" * 50)
    print("基本语音转换示例")
    print("=" * 50)

    client = VoiceConversionClient()

    # 检查API健康状态
    print("检查API健康状态...")
    health = client.health_check()
    if health["status"] != "healthy":
        print(f"API不健康: {health}")
        return
    print(f"API状态: {health['status']}")
    print(f"模型已加载: {health['models_loaded']}")
    print(f"设备: {health['device']}")

    # 配置文件路径（请替换为实际文件路径）
    source_path = "examples/source/yae_0.wav"
    target_path = "examples/reference/dingzhen_0.wav"

    # 检查文件是否存在
    if not os.path.exists(source_path):
        print(f"源文件不存在: {source_path}")
        return
    if not os.path.exists(target_path):
        print(f"参考文件不存在: {target_path}")
        return

    print(f"\n开始转换...")
    print(f"源文件: {source_path}")
    print(f"参考文件: {target_path}")

    start_time = time.time()

    # 转换音频
    result = client.convert_with_files(
        source_path=source_path,
        target_path=target_path,
        diffusion_steps=50,
        output_format="mp3"
    )

    processing_time = time.time() - start_time

    if result["success"]:
        print(f"\n✓ 转换成功!")
        print(f"处理时间: {processing_time:.2f}秒 (服务器报告: {result['processing_time']:.2f}秒)")
        print(f"输出格式: {result['output_format']}")

        if result["input_info"]:
            source_info = result["input_info"]["source"]
            target_info = result["input_info"]["target"]
            print(f"\n源音频信息:")
            print(f"  时长: {source_info['duration']:.2f}秒")
            print(f"  采样率: {source_info['sample_rate']}Hz")
            print(f"  文件大小: {source_info['file_size']:,}字节")

            print(f"\n参考音频信息:")
            print(f"  时长: {target_info['duration']:.2f}秒")
            print(f"  采样率: {target_info['sample_rate']}Hz")
            print(f"  文件大小: {target_info['file_size']:,}字节")

        if result["full_output_path"]:
            print(f"\n输出文件路径: {result['full_output_path']}")

            # 复制到当前目录
            import shutil
            output_name = f"output_basic.{result['output_format']}"
            shutil.copy2(result["full_output_path"], output_name)
            print(f"已复制到: {output_name}")

    else:
        print(f"\n✗ 转换失败: {result['message']}")


def example_base64_conversion():
    """Base64编码转换示例"""
    print("\n" + "=" * 50)
    print("Base64编码转换示例")
    print("=" * 50)

    client = VoiceConversionClient()

    source_path = "examples/source/yae_0.wav"
    target_path = "examples/reference/dingzhen_0.wav"

    if not os.path.exists(source_path) or not os.path.exists(target_path):
        print("示例文件不存在，跳过此示例")
        return

    print("使用Base64编码传输音频...")

    result = client.convert_with_base64(
        source_path=source_path,
        target_path=target_path,
        diffusion_steps=50,
        output_format="ogg"
    )

    if result["success"]:
        print("✓ Base64转换成功!")

        if result["full_output_base64"]:
            # 保存Base64结果
            output_name = "output_base64.ogg"
            client.save_base64_audio(result["full_output_base64"], output_name)
            print(f"已保存到: {output_name}")

    else:
        print(f"✗ Base64转换失败: {result['message']}")


def example_file_upload():
    """文件上传转换示例"""
    print("\n" + "=" * 50)
    print("文件上传转换示例")
    print("=" * 50)

    client = VoiceConversionClient()

    source_path = "examples/source/jay_0.wav"
    target_path = "examples/reference/azuma_0.wav"

    if not os.path.exists(source_path) or not os.path.exists(target_path):
        print("示例文件不存在，跳过此示例")
        return

    print("使用文件上传方式转换...")

    result = client.convert_with_upload(
        source_path=source_path,
        target_path=target_path,
        diffusion_steps=50,
        output_format="mp3",
        top_p=0.9,
        temperature=1.0,
        return_base64=True
    )

    if result["success"]:
        print("✓ 文件上传转换成功!")

        if result["full_output_base64"]:
            output_name = "output_upload.mp3"
            client.save_base64_audio(result["full_output_base64"], output_name)
            print(f"已保存到: {output_name}")

    else:
        print(f"✗ 文件上传转换失败: {result['message']}")


def example_style_conversion():
    """风格转换示例"""
    print("\n" + "=" * 50)
    print("风格转换示例")
    print("=" * 50)

    client = VoiceConversionClient()

    source_path = "examples/source/yae_0.wav"
    target_path = "examples/reference/dingzhen_0.wav"

    if not os.path.exists(source_path) or not os.path.exists(target_path):
        print("示例文件不存在，跳过此示例")
        return

    print("启用风格转换...")

    result = client.convert_with_files(
        source_path=source_path,
        target_path=target_path,
        diffusion_steps=50,
        output_format="mp3",
        convert_style=True,
        similarity_cfg_rate=0.8,
        intelligibility_cfg_rate=0.2
    )

    if result["success"]:
        print("✓ 风格转换成功!")

        if result["full_output_path"]:
            output_name = "output_style.mp3"
            import shutil
            shutil.copy2(result["full_output_path"], output_name)
            print(f"已保存到: {output_name}")

    else:
        print(f"✗ 风格转换失败: {result['message']}")


def example_anonymization():
    """匿名化示例"""
    print("\n" + "=" * 50)
    print("语音匿名化示例")
    print("=" * 50)

    client = VoiceConversionClient()

    source_path = "examples/source/yae_0.wav"
    target_path = "examples/reference/dingzhen_0.wav"

    if not os.path.exists(source_path) or not os.path.exists(target_path):
        print("示例文件不存在，跳过此示例")
        return

    print("启用匿名化模式...")

    result = client.convert_with_files(
        source_path=source_path,
        target_path=target_path,
        diffusion_steps=50,
        output_format="mp3",
        anonymization_only=True,
        repetition_penalty=1.5
    )

    if result["success"]:
        print("✓ 匿名化转换成功!")

        if result["full_output_path"]:
            output_name = "output_anonymous.mp3"
            import shutil
            shutil.copy2(result["full_output_path"], output_name)
            print(f"已保存到: {output_name}")

    else:
        print(f"✗ 匿名化转换失败: {result['message']}")


def example_batch_processing():
    """批量处理示例"""
    print("\n" + "=" * 50)
    print("批量处理示例")
    print("=" * 50)

    client = VoiceConversionClient()

    # 示例文件对
    file_pairs = [
        ("examples/source/yae_0.wav", "examples/reference/dingzhen_0.wav"),
        ("examples/source/jay_0.wav", "examples/reference/azuma_0.wav"),
    ]

    # 过滤存在的文件
    existing_pairs = []
    for source, target in file_pairs:
        if os.path.exists(source) and os.path.exists(target):
            existing_pairs.append((source, target))

    if not existing_pairs:
        print("没有找到示例文件，跳过批量处理")
        return

    print(f"处理 {len(existing_pairs)} 个音频对...")

    def process_pair(index, source_path, target_path):
        """处理单个音频对"""
        try:
            result = client.convert_with_files(
                source_path=source_path,
                target_path=target_path,
                diffusion_steps=50,
                output_format="mp3",
                return_base64=True
            )

            if result["success"]:
                output_name = f"output_batch_{index}.mp3"
                if result["full_output_base64"]:
                    client.save_base64_audio(result["full_output_base64"], output_name)

                return {
                    "index": index,
                    "success": True,
                    "output": output_name,
                    "time": result["processing_time"]
                }
            else:
                return {
                    "index": index,
                    "success": False,
                    "error": result["message"]
                }
        except Exception as e:
            return {
                "index": index,
                "success": False,
                "error": str(e)
            }

    # 并发处理
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for i, (source, target) in enumerate(existing_pairs):
            future = executor.submit(process_pair, i, source, target)
            futures.append(future)

        results = []
        for future in futures:
            results.append(future.result())

    # 显示结果
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"\n批量处理完成!")
    print(f"成功: {len(successful)}/{len(results)}")
    print(f"失败: {len(failed)}/{len(results)}")

    if successful:
        total_time = sum(r["time"] for r in successful)
        print(f"总处理时间: {total_time:.2f}秒")

        print("\n成功转换的文件:")
        for result in successful:
            print(f"  - {result['output']} (处理时间: {result['time']:.2f}秒)")

    if failed:
        print("\n失败的文件:")
        for result in failed:
            print(f"  - 文件 {result['index']}: {result['error']}")


def example_parameter_tuning():
    """参数调优示例"""
    print("\n" + "=" * 50)
    print("参数调优示例")
    print("=" * 50)

    client = VoiceConversionClient()

    source_path = "examples/source/yae_0.wav"
    target_path = "examples/reference/dingzhen_0.wav"

    if not os.path.exists(source_path) or not os.path.exists(target_path):
        print("示例文件不存在，跳过参数调优示例")
        return

    # 不同的参数组合
    parameter_sets = [
        {
            "name": "快速模式",
            "params": {
                "diffusion_steps": 20,
                "temperature": 0.7,
                "output_format": "mp3"
            }
        },
        {
            "name": "高质量模式",
            "params": {
                "diffusion_steps": 80,
                "temperature": 1.0,
                "top_p": 0.9,
                "output_format": "wav"
            }
        },
        {
            "name": "创意模式",
            "params": {
                "diffusion_steps": 50,
                "temperature": 1.5,
                "top_p": 0.95,
                "repetition_penalty": 1.2,
                "output_format": "mp3"
            }
        },
        {
            "name": "稳定模式",
            "params": {
                "diffusion_steps": 50,
                "temperature": 0.8,
                "top_p": 0.8,
                "repetition_penalty": 1.5,
                "intelligibility_cfg_rate": 0.8,
                "similarity_cfg_rate": 0.5,
                "output_format": "ogg"
            }
        }
    ]

    for config in parameter_sets:
        print(f"\n测试 {config['name']}...")

        start_time = time.time()
        result = client.convert_with_files(
            source_path=source_path,
            target_path=target_path,
            **config["params"]
        )
        end_time = time.time()

        if result["success"]:
            output_name = f"output_tuning_{config['name'].replace(' ', '_')}.{config['params']['output_format']}"

            if result["full_output_path"]:
                import shutil
                shutil.copy2(result["full_output_path"], output_name)

            print(f"✓ 成功!")
            print(f"  处理时间: {end_time - start_time:.2f}秒")
            print(f"  输出文件: {output_name}")
            print(f"  服务器时间: {result['processing_time']:.2f}秒")
        else:
            print(f"✗ 失败: {result['message']}")


def main():
    """运行所有示例"""
    print("Seed Voice Conversion V2 API - 客户端示例")
    print("=" * 60)

    try:
        # 运行各种示例
        example_basic_conversion()
        example_base64_conversion()
        example_file_upload()
        example_style_conversion()
        example_anonymization()
        example_batch_processing()
        example_parameter_tuning()

        print("\n" + "=" * 60)
        print("所有示例运行完成!")
        print("请检查当前目录中的输出文件。")

    except KeyboardInterrupt:
        print("\n用户中断了示例运行")
    except Exception as e:
        print(f"\n运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()