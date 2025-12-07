# Seed Voice Conversion V2 API

## 项目概述

Seed Voice Conversion V2 API 提供了完整的语音转换功能，支持零样本语音转换、歌声转换、风格转换和匿名化。API与Web界面功能完全相同，支持多种音频格式，并提供丰富的参数调优选项。

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装API依赖
source /opt/venv/seedvc/bin/activate
pip install -r requirements_api.txt

# 或者直接安装
pip install fastapi uvicorn[standard] pydantic python-multipart requests
```

### 2. 启动API服务器

```bash
# 基本启动
python api_v2.py

# 使用启动脚本
python start_api.py

# 指定端口
python api_v2.py --port 8080

# 启用模型编译（更快速度）
python api_v2.py --compile
```

### 3. 访问API文档

启动后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📋 功能特性

### ✅ 核心功能
- **零样本语音转换**: 无需训练即可转换任意语音
- **多格式支持**: WAV、MP3、OGG输入输出
- **智能音频分割**: 最长240秒，静音处智能分割
- **高音频质量**: 专业级音频处理
- **参数调优**: 完整的生成参数控制

### ✅ 高级功能
- **风格转换**: 支持语音风格迁移
- **匿名化**: 生成匿名语音输出
- **Base64支持**: 便于Web应用集成
- **文件上传**: 直接上传音频文件
- **批量处理**: 支持并发处理
- **错误处理**: 完善的错误处理和恢复

### ✅ 技术特性
- **RESTful API**: 标准的HTTP接口
- **自动文档**: Swagger/OpenAPI文档
- **类型安全**: Pydantic模型验证
- **高性能**: 支持模型编译优化
- **易于集成**: 简单的客户端库

## 📁 文件结构

```
seed-vc/
├── api_v2.py              # API服务器主文件
├── client_examples.py      # 客户端使用示例
├── start_api.py           # 快速启动脚本
├── requirements_api.txt   # API依赖包
├── API_DOCUMENTATION.md   # 详细API文档
├── README_API.md         # API概述（本文件）
└── examples/             # 示例音频文件
    ├── source/           # 源音频示例
    └── reference/        # 参考音频示例
```

## 🛠️ 使用方法

### 1. 基本调用（JSON格式）

```python
import requests

data = {
    "source_audio_path": "/path/to/source.wav",
    "target_audio_path": "/path/to/reference.wav",
    "diffusion_steps": 50,
    "output_format": "mp3"
}

response = requests.post("http://localhost:8000/convert", json=data)
result = response.json()
```

### 2. 文件上传方式

```bash
curl -X POST "http://localhost:8000/convert/files" \
  -F "source_audio=@source.wav" \
  -F "target_audio=@reference.wav" \
  -F "output_format=mp3"
```

### 3. Base64编码方式

```python
import base64
import requests

# 编码音频文件
with open("source.wav", "rb") as f:
    source_base64 = base64.b64encode(f.read()).decode()

data = {
    "source_audio_base64": source_base64,
    "target_audio_base64": target_base64,
    "output_format": "mp3"
}

response = requests.post("http://localhost:8000/convert", json=data)
```

### 4. 使用客户端库

```python
from client_examples import VoiceConversionClient

client = VoiceConversionClient("http://localhost:8000")

result = client.convert_with_files(
    source_path="source.wav",
    target_path="reference.wav",
    diffusion_steps=50,
    output_format="mp3"
)
```

## 📊 API参数说明

### 核心参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `diffusion_steps` | int | 30 | 扩散步数，影响质量 |
| `length_adjust` | float | 1.0 | 长度调整（0.5-2.0） |
| `output_format` | string | "wav" | 输出格式（wav/mp3/ogg） |

### 质量控制参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `top_p` | float | 0.9 | Top-p采样（0.1-1.0） |
| `temperature` | float | 1.0 | 温度参数（0.1-2.0） |
| `repetition_penalty` | float | 1.0 | 重复惩罚（1.0-3.0） |

### 高级参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `convert_style` | bool | false | 启用风格转换 |
| `anonymization_only` | bool | false | 仅匿名化模式 |
| `intelligibility_cfg_rate` | float | 0.5 | 可懂性CFG（0.0-1.0） |
| `similarity_cfg_rate` | float | 0.5 | 相似性CFG（0.0-1.0） |

## 🔧 配置选项

### 启动参数

```bash
python api_v2.py [OPTIONS]

Options:
  --host TEXT         绑定主机地址（默认: 0.0.0.0）
  --port INTEGER      绑定端口（默认: 8000）
  --compile           启用模型编译（更快但更多显存）
  --ar-checkpoint-path TEXT  AR模型检查点路径
  --cfm-checkpoint-path TEXT CFM模型检查点路径
```

### 环境变量

```bash
# 设置CUDA设备
export CUDA_VISIBLE_DEVICES=0

# 设置最大工作线程
export OMP_NUM_THREADS=4
```

## 📈 性能优化

### 1. 模型编译
```bash
python api_v2.py --compile
```
编译后速度提升30-50%，但需要更多显存。

### 2. 批量处理
使用并发请求处理多个音频文件：
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(convert_audio, src, tgt)
               for src, tgt in audio_pairs]
    results = [f.result() for f in futures]
```

### 3. 格式选择
- **WAV**: 最高质量，文件较大
- **MP3**: 平衡质量和大小，推荐
- **OGG**: 最小文件大小，适合传输

### 4. 参数调优
- **快速预览**: diffusion_steps=20
- **高质量**: diffusion_steps=50-100
- **创意模式**: temperature=1.5, top_p=0.95
- **稳定模式**: temperature=0.8, repetition_penalty=1.5

## 🚨 限制说明

### 系统要求
- **Python**: 3.8+
- **GPU**: 推荐NVIDIA GPU，8GB+显存
- **内存**: 16GB+ RAM
- **存储**: 10GB+ 可用空间

### 音频限制
- **输入格式**: WAV, MP3, OGG
- **采样率**: 自动重采样到22050Hz
- **声道**: 自动转为单声道
- **参考音频**: 最长120秒
- **源音频**: 最长240秒（自动分割）

### 并发限制
- **推荐并发**: 最多3个请求
- **单机负载**: 根据显存大小调整
- **网络**: 高延迟网络建议使用Base64

## 🔍 故障排除

### 常见问题

1. **模型加载失败**
   ```
   检查 checkpoints 文件是否存在
   确认 GPU 驱动正常
   检查显存是否足够
   ```

2. **音频文件错误**
   ```
   确认文件路径正确
   检查文件格式是否支持
   验证文件未损坏
   ```

3. **连接超时**
   ```
   检查网络连接
   增加请求超时时间
   减少并发请求数量
   ```

4. **内存不足**
   ```
   减少并发请求
   使用较小的音频文件
   禁用模型编译
   清理临时文件
   ```

### 日志调试

```bash
# 启用详细日志
export PYTHONPATH=/path/to/seed-vc
python api_v2.py --host 127.0.0.1 --port 8000

# 监控GPU使用
nvidia-smi -l 1
```

## 📞 支持

### 文档资源
- [详细API文档](API_DOCUMENTATION.md)
- [客户端示例](client_examples.py)
- [Swagger UI](http://localhost:8000/docs)

### 获取帮助
1. 查看 API 文档中的参数说明
2. 运行客户端示例代码
3. 检查故障排除指南
4. 查看项目 GitHub Issues

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目遵循原项目的许可证条款。

---

**开始使用语音转换API吧！** 🎙️✨