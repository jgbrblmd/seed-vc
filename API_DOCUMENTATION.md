# Seed Voice Conversion V2 API Documentation

## 概述

Seed Voice Conversion V2 API 提供了与Web界面完全相同的语音转换功能，支持零样本语音转换、歌声转换、风格转换和匿名化。支持多种音频格式（WAV、MP3、OGG）的输入和输出。

## 功能特性

- ✅ **零样本语音转换**: 无需训练即可转换任意语音
- ✅ **多格式支持**: 支持WAV、MP3、OGG格式的输入和输出
- ✅ **智能音频分割**: 支持最长240秒的音频处理，在静音处智能分割
- ✅ **风格转换**: 支持语音风格的转换
- ✅ **匿名化**: 生成匿名的语音输出
- ✅ **参数调优**: 完整的生成参数控制
- ✅ **Base64编码**: 支持Base64编码的音频传输
- ✅ **文件上传**: 支持直接上传音频文件

## 快速开始

### 1. 启动API服务

```bash
# 基本启动
python api_v2.py

# 指定端口和主机
python api_v2.py --host 0.0.0.0 --port 8000

# 启用模型编译（更快速度，更多显存）
python api_v2.py --compile

# 使用自定义检查点
python api_v2.py --ar-checkpoint-path /path/to/ar.pth --cfm-checkpoint-path /path/to/cfm.pth
```

### 2. 访问API文档

启动后访问以下地址查看交互式API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. 健康检查

```bash
curl http://localhost:8000/health
```

## API 端点

### 1. POST /convert - 语音转换（JSON格式）

通过JSON格式提交请求，支持文件路径或Base64编码的音频。

#### 请求参数

| 参数名 | 类型 | 必需 | 默认值 | 范围 | 描述 |
|--------|------|------|--------|------|------|
| source_audio_path | string | 否 | - | - | 源音频文件路径 |
| source_audio_base64 | string | 否 | - | - | Base64编码的源音频 |
| target_audio_path | string | 否 | - | - | 参考音频文件路径 |
| target_audio_base64 | string | 否 | - | - | Base64编码的参考音频 |
| diffusion_steps | int | 否 | 30 | 1-200 | 扩散步数 |
| length_adjust | float | 否 | 1.0 | 0.5-2.0 | 长度调整系数 |
| intelligibility_cfg_rate | float | 否 | 0.5 | 0.0-1.0 | 可懂性CFG率 |
| similarity_cfg_rate | float | 否 | 0.5 | 0.0-1.0 | 相似性CFG率 |
| top_p | float | 否 | 0.9 | 0.1-1.0 | Top-p采样参数 |
| temperature | float | 否 | 1.0 | 0.1-2.0 | 温度参数 |
| repetition_penalty | float | 否 | 1.0 | 1.0-3.0 | 重复惩罚 |
| convert_style | bool | 否 | false | - | 启用风格转换 |
| anonymization_only | bool | 否 | false | - | 仅匿名化模式 |
| output_format | string | 否 | "wav" | wav/mp3/ogg | 输出格式 |
| return_base64 | bool | 否 | false | - | 返回Base64编码 |
| cleanup_temp_files | bool | 否 | true | - | 清理临时文件 |

#### 使用文件路径的示例

```bash
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "source_audio_path": "/path/to/source.wav",
    "target_audio_path": "/path/to/reference.wav",
    "diffusion_steps": 50,
    "output_format": "mp3",
    "return_base64": false
  }'
```

#### 使用Base64编码的示例

```bash
# 首先编码音频文件
SOURCE_BASE64=$(base64 -w 0 /path/to/source.wav)
TARGET_BASE64=$(base64 -w 0 /path/to/reference.wav)

# 然后发送请求
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: application/json" \
  -d "{
    \"source_audio_base64\": \"$SOURCE_BASE64\",
    \"target_audio_base64\": \"$TARGET_BASE64\",
    \"diffusion_steps\": 50,
    \"output_format\": \"mp3\"
  }"
```

### 2. POST /convert/files - 语音转换（文件上传）

通过multipart/form-data上传音频文件。

#### 请求参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| source_audio | file | 是 | - | 源音频文件 |
| target_audio | file | 是 | - | 参考音频文件 |
| diffusion_steps | int | 否 | 30 | 扩散步数 |
| length_adjust | float | 否 | 1.0 | 长度调整系数 |
| intelligibility_cfg_rate | float | 否 | 0.5 | 可懂性CFG率 |
| similarity_cfg_rate | float | 否 | 0.5 | 相似性CFG率 |
| top_p | float | 否 | 0.9 | Top-p采样参数 |
| temperature | float | 否 | 1.0 | 温度参数 |
| repetition_penalty | float | 否 | 1.0 | 重复惩罚 |
| convert_style | bool | 否 | false | 启用风格转换 |
| anonymization_only | bool | 否 | false | 仅匿名化模式 |
| output_format | string | 否 | "wav" | 输出格式 |
| return_base64 | bool | 否 | false | 返回Base64编码 |

#### 文件上传示例

```bash
curl -X POST "http://localhost:8000/convert/files" \
  -F "source_audio=@/path/to/source.wav" \
  -F "target_audio=@/path/to/reference.wav" \
  -F "diffusion_steps=50" \
  -F "output_format=mp3" \
  -F "return_base64=false"
```

## 响应格式

```json
{
  "success": true,
  "message": "Voice conversion completed successfully",
  "streaming_output_path": "/tmp/streaming_output.mp3",
  "full_output_path": "/tmp/full_output.mp3",
  "streaming_output_base64": "base64_encoded_streaming_audio",
  "full_output_base64": "base64_encoded_full_audio",
  "processing_time": 12.34,
  "output_format": "mp3",
  "input_info": {
    "source": {
      "duration": 30.5,
      "sample_rate": 22050,
      "channels": 1,
      "file_size": 1024000,
      "file_format": "wav"
    },
    "target": {
      "duration": 15.2,
      "sample_rate": 22050,
      "channels": 1,
      "file_size": 512000,
      "file_format": "wav"
    }
  }
}
```

## Python 客户端示例

### 基本使用

```python
import requests
import json

# API配置
API_URL = "http://localhost:8000/convert"

# 请求数据
data = {
    "source_audio_path": "/path/to/source.wav",
    "target_audio_path": "/path/to/reference.wav",
    "diffusion_steps": 50,
    "output_format": "mp3",
    "return_base64": True
}

# 发送请求
response = requests.post(API_URL, json=data)
result = response.json()

if result["success"]:
    print("转换成功!")
    print(f"处理时间: {result['processing_time']:.2f}秒")

    if result["full_output_base64"]:
        # 解码Base64音频
        import base64
        audio_data = base64.b64decode(result["full_output_base64"])

        # 保存到文件
        with open("output.mp3", "wb") as f:
            f.write(audio_data)

        print("音频已保存到 output.mp3")
else:
    print(f"转换失败: {result['message']}")
```

### 文件上传示例

```python
import requests

# API配置
API_URL = "http://localhost:8000/convert/files"

# 文件路径
source_file = "/path/to/source.wav"
target_file = "/path/to/reference.wav"

# 准备文件和数据
files = {
    'source_audio': open(source_file, 'rb'),
    'target_audio': open(target_file, 'rb')
}

data = {
    'diffusion_steps': 50,
    'output_format': 'mp3',
    'convert_style': True
}

# 发送请求
response = requests.post(API_URL, files=files, data=data)
result = response.json()

# 关闭文件
files['source_audio'].close()
files['target_audio'].close()

if result["success"]:
    print(f"转换成功! 输出文件: {result['full_output_path']}")
else:
    print(f"转换失败: {result['message']}")
```

### 高级用法 - 批量处理

```python
import requests
import os
from concurrent.futures import ThreadPoolExecutor
import time

API_URL = "http://localhost:8000/convert"

def convert_audio_pair(source_path, target_path, output_format="mp3"):
    """转换一对音频文件"""
    data = {
        "source_audio_path": source_path,
        "target_audio_path": target_path,
        "diffusion_steps": 50,
        "output_format": output_format,
        "return_base64": True
    }

    response = requests.post(API_URL, json=data)
    result = response.json()

    if result["success"]:
        # 保存结果
        import base64
        audio_data = base64.b64decode(result["full_output_base64"])
        output_name = f"converted_{os.path.basename(source_path)}"

        with open(output_name, "wb") as f:
            f.write(audio_data)

        return {
            "success": True,
            "output_file": output_name,
            "processing_time": result["processing_time"]
        }
    else:
        return {
            "success": False,
            "error": result["message"]
        }

# 批量处理示例
source_files = ["source1.wav", "source2.wav", "source3.wav"]
target_files = ["ref1.wav", "ref2.wav", "ref3.wav"]

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = []
    for i, (src, tgt) in enumerate(zip(source_files, target_files)):
        future = executor.submit(convert_audio_pair, src, tgt)
        futures.append(future)

    for i, future in enumerate(futures):
        result = future.result()
        if result["success"]:
            print(f"文件 {i+1} 转换成功: {result['output_file']}")
        else:
            print(f"文件 {i+1} 转换失败: {result['error']}")
```

## 参数调优指南

### 基础参数

- **diffusion_steps**: 扩散步数，影响质量
  - 30: 默认值，平衡速度和质量
  - 50-100: 高质量，处理时间较长
  - 1-20: 快速预览，质量较低

- **length_adjust**: 长度调整
  - 1.0: 保持原始长度
  - 0.8: 加速20%
  - 1.2: 减慢20%

### 采样参数

- **top_p**: 控制多样性
  - 0.9: 推荐值，平衡多样性和质量
  - 0.7: 更保守，质量更稳定
  - 1.0: 最大多样性

- **temperature**: 控制随机性
  - 1.0: 推荐值
  - 0.7: 更确定性
  - 1.5: 更多变化

- **repetition_penalty**: 防止重复
  - 1.0: 不惩罚重复
  - 1.5: 推荐值
  - 3.0: 强烈避免重复

### CFG参数

- **intelligibility_cfg_rate**: 可懂性控制
  - 0.5: 推荐值
  - 0.0: 不可懂性约束
  - 1.0: 强可懂性约束

- **similarity_cfg_rate**: 相似性控制
  - 0.5: 推荐值
  - 0.0: 忽略参考音频
  - 1.0: 强制与参考音频相似

## 错误处理

### 常见错误码

- **400**: 请求参数错误
- **404**: 文件未找到
- **500**: 服务器内部错误

### 常见错误信息

1. **"Either source_audio_path or source_audio_base64 must be provided"**
   - 需要提供源音频路径或Base64编码

2. **"Invalid audio file"**
   - 音频文件格式不支持或文件损坏

3. **"Models not loaded"**
   - 模型未正确加载，请检查初始化

4. **"Audio file not found"**
   - 指定的音频文件路径不存在

## 性能优化

### 1. 模型编译

```bash
python api_v2.py --compile
```

编译后速度提升约30-50%，但需要更多显存。

### 2. 批量处理

使用多个并发请求处理多个音频文件。

### 3. 格式选择

- WAV: 最高质量，文件较大
- MP3: 平衡质量和大小
- OGG: 最小文件大小，适合网络传输

### 4. 音频长度

支持最长240秒的音频，超过会自动分割。

## 限制说明

1. **音频格式**: 支持WAV、MP3、OGG，会自动转换为单声道
2. **采样率**: 自动重采样到22050Hz
3. **最大长度**: 参考音频最长120秒，源音频最长240秒
4. **并发处理**: 建议不超过3个并发请求
5. **GPU内存**: 建议至少8GB显存，推荐16GB以上

## 更新日志

### v2.0.0
- 支持多种音频格式
- 智能音频分割
- Base64编码支持
- 文件上传接口
- 完整的参数控制
- 错误处理优化

---

如有问题或建议，请查看GitHub仓库或联系开发团队。