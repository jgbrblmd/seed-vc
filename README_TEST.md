# API vs Web 界面一致性测试

## 📋 测试目标

本测试脚本用于验证Seed Voice Conversion V2 API与Web界面的功能一致性，确保：
- API能生成与Web界面相同质量的音频
- 所有参数按预期工作
- 支持多种音频格式输出
- 处理性能符合预期

## 🚀 运行测试

### 前提条件
1. **API服务器已启动**
   ```bash
   python api_v2.py
   ```

2. **API服务器健康状态**
   ```bash
   curl http://localhost:8000/health
   # 应该返回: {"status": "healthy", "models_loaded": true, ...}
   ```

### 运行测试脚本

```bash
python test_api_vs_web.py
```

## 📊 测试内容

### 测试样本
使用与`app_vc_v2.py`中相同的示例：

1. **示例1**: 雅生音 → 丁真音
   - 源音频: `examples/source/yae_0.wav`
   - 参考音频: `examples/reference/dingzhen_0.wav`

2. **示例2**: 周杰伦音 → 东丈音
   - 源音频: `examples/source/jay_0.wav`
   - 参考音频: `examples/reference/azuma_0.wav`

### 输出格式
每个示例生成3种格式：
- **WAV**: 无损格式，最高质量
- **MP3**: 压缩格式，平衡质量和大小
- **OGG**: 开源格式，文件最小

### 生成参数
使用与Web界面相同的默认参数：
```json
{
    "diffusion_steps": 50,
    "length_adjust": 1.0,
    "intelligibility_cfg_rate": 0.5,
    "similarity_cfg_rate": 0.5,
    "top_p": 0.9,
    "temperature": 1.0,
    "repetition_penalty": 1.0,
    "convert_style": false,
    "anonymization_only": false
}
```

## 📁 输出文件

### 文件命名
- `example_1_converted.wav`
- `example_1_converted.mp3`
- `example_1_converted.ogg`
- `example_2_converted.wav`
- `example_2_converted.mp3`
- `example_2_converted.ogg`

### 输出目录
所有文件保存在：`/tmp/seedvc/`

### 测试报告
详细的测试结果保存在：`/tmp/seedvc/test_report.json`

## 🔍 验证步骤

### 1. 音质对比
```bash
# 播放生成的音频
ls /tmp/seedvc/
# 使用音频播放器比较不同格式的音质
```

### 2. 参数验证
检查参数是否按预期影响输出：
- `diffusion_steps`: 影响音频质量
- `temperature`: 影响音频多样性
- `top_p`: 影响生成稳定性

### 3. 性能分析
- 处理时间与音频长度的关系
- 不同格式的文件大小对比
- API响应时间分析

## 📈 预期结果

### 成功标准
- ✅ 6个文件全部生成成功（成功率100%）
- ✅ 音质与Web界面生成的音频一致
- ✅ 参数按预期影响输出
- ✅ 处理时间合理（通常30-60秒/分钟音频）

### 常见问题排查

#### 问题1: 连接失败
```
❌ 无法连接到API服务器
```
**解决方案**:
- 确认API服务器正在运行
- 检查端口8000是否可用
- 验证防火墙设置

#### 问题2: 音频文件不存在
```
❌ 源文件不存在: examples/source/yae_0.wav
```
**解决方案**:
- 确认示例文件在正确位置
- 检查文件权限
- 重新下载示例文件

#### 问题3: 转换失败
```
❌ 转换失败: [错误信息]
```
**解决方案**:
- 检查API日志
- 验证音频文件格式
- 检查GPU内存使用情况

#### 问题4: 音质不一致
```
生成的音频与Web界面不同
```
**解决方案**:
- 确认使用相同参数
- 检查模型版本
- 验证音频处理流程

## 🛠️ 高级测试

### 自定义参数测试
可以修改`test_api_vs_web.py`中的`EXAMPLES`来测试不同参数：

```python
# 风格转换测试
{
    "convert_style": True,
    "similarity_cfg_rate": 0.8,
    "intelligibility_cfg_rate": 0.2
}

# 高质量测试
{
    "diffusion_steps": 80,
    "temperature": 0.8,
    "top_p": 0.9
}

# 快速预览测试
{
    "diffusion_steps": 20,
    "temperature": 1.2,
    "top_p": 0.95
}
```

### 批量测试
如果要测试多个音频文件对：

```python
AUDIO_PAIRS = [
    ("source1.wav", "ref1.wav"),
    ("source2.wav", "ref2.wav"),
    # ... 更多文件对
]
```

## 📋 测试报告解读

测试报告包含以下信息：
- 测试时间和日期
- 成功/失败的转换数量
- 文件大小和处理时间
- 详细的错误信息

### 报告示例
```json
{
  "test_time": "2025-12-07 12:00:00",
  "examples_tested": 2,
  "formats_tested": 3,
  "successful_conversions": 6,
  "failed_conversions": 0,
  "success_rate": 1.0,
  "output_directory": "/tmp/seedvc"
}
```

## 🎯 结论建议

### 测试成功（成功率 ≥ 80%）
- ✅ API与Web界面功能一致
- ✅ 可以用于生产环境
- ✅ 参数配置正确

### 测试部分成功（50% ≤ 成功率 < 80%）
- ⚠️ 基本功能正常
- ⚠️ 部分参数需要调整
- ⚠️ 建议进一步调试

### 测试失败（成功率 < 50%）
- ❌ 存在严重配置问题
- ❌ 需要重新检查设置
- ❌ 建议查看详细日志

---

运行测试后，请听取生成的音频文件，验证与Web界面的音质一致性！