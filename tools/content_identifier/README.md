# Content Identifier Function

## 功能描述

这个工具接受图片URI作为输入，使用自然语言输出图片的整体内容，并通过天气和室内外环境判断出拍摄时的亮度高低。

## 功能特性

1. **图像内容分析**: 使用视觉语言模型分析图像中的物体、场景、环境特征等
2. **亮度判断**: 结合图像统计分析和内容理解，判断拍摄时的光照条件
3. **环境识别**: 识别室内外环境、天气状况等影响因素
4. **中文输出**: 提供自然流畅的中文描述

## 输入格式

```json
{
    "image_uri": "https://example.com/image.jpg"
}
```

支持的图片URI格式：
- HTTP/HTTPS URL
- Base64编码的data URI
- 本地文件路径

## 输出格式

```json
{
    "content": "这是一张室外晴天的照片，可以看到蓝天白云，阳光明媚。照片中有建筑物和绿色植物，整体光照充足。",
    "brightness": "明亮 - 室外晴天，阳光充足"
}
```

### 亮度级别说明

- **非常昏暗**: 夜晚或极低光照环境，主要依靠人工照明
- **昏暗**: 夜晚环境下有适度的人工照明
- **较暗**: 室外阴天环境或室内光照不足
- **中等亮度**: 室外多云天气或室内有良好照明
- **明亮**: 室外晴天或室内光照充足
- **非常明亮**: 强烈阳光或高强度照明，可能存在过曝

## 配置说明

### 基本配置

```yaml
functions:
  content_identifier:
    _type: content_identifier
    api_key: ${DASHSCOPE_API_KEY}
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name: "qwen-vl-max-latest"

workflow:
  _type: content_identifier
```

### API配置选项

#### 阿里云DashScope（推荐）
```yaml
functions:
  content_identifier:
    _type: content_identifier
    api_key: ${DASHSCOPE_API_KEY}  # 阿里云API密钥
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name: "qwen-vl-max-latest"  # 或 qwen-vl-plus-latest
```

#### OpenAI API
```yaml
functions:
  content_identifier:
    _type: content_identifier
    api_key: ${OPENAI_API_KEY}  # OpenAI API密钥
    base_url: "https://api.openai.com/v1"  # 可选，默认OpenAI endpoint
    model_name: "gpt-4o"  # 或其他支持视觉的模型
```

### 支持的视觉模型

#### 阿里云DashScope模型（推荐）
- `qwen-vl-max-latest` - 通义千问视觉语言大模型
- `qwen-vl-plus-latest` - 通义千问视觉语言模型（轻量版）

#### OpenAI模型
- `gpt-4-vision-preview`
- `gpt-4o`
- `gpt-4o-mini`

#### NVIDIA NIM模型
- `nvidia/neva-22b`
- `nvidia/llava-1.6-mistral-7b`
- 其他支持视觉的NIM模型

## 使用示例

### 1. 启动服务

```bash
nat run --config example_config.yaml
```

### 2. 发送请求

```bash
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "image_uri": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"
  }'
```

### 3. 设置环境变量

使用阿里云DashScope API：
```bash
export DASHSCOPE_API_KEY="your_dashscope_api_key_here"
```

或使用OpenAI API：
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 3. 响应示例

```json
{
  "content": "这是一张温馨的室内照片，显示了一位年轻女孩和一只可爱的小狗。女孩坐在沙发上，怀里抱着一只小型犬，两者都显得非常放松和快乐。室内环境明亮温暖，可以看到自然光从窗户透进来，整体光照条件良好。背景中有家具和装饰品，营造出舒适的家庭氛围。",
  "brightness": "明亮 - 室内有良好的自然光照"
}
```

## 技术实现

### 图像处理
- 使用PIL库加载和处理图像
- 支持多种图像格式（JPEG、PNG等）
- 自动转换为RGB模式进行分析

### 亮度分析算法
1. **统计分析**: 计算图像的平均亮度、亮度分布
2. **内容理解**: 结合视觉模型对环境的判断
3. **综合评估**: 基于多个因素确定最终亮度级别

### 环境判断因素
- 室内外环境识别
- 天气状况分析
- 光源类型判断（自然光/人工照明）
- 时间推断（白天/夜晚）

## 依赖要求

```
pillow>=9.0.0
numpy>=1.20.0
requests>=2.25.0
openai>=1.0.0
```

## 注意事项

1. **API密钥**: 需要有效的阿里云DashScope API密钥或OpenAI API密钥
2. **网络图片**: 需要确保图片URL可访问，函数会设置30秒超时
3. **图片大小**: 建议图片大小不超过10MB以确保处理效率
4. **调用频率**: 注意API的调用频率和成本限制
5. **隐私安全**: 处理敏感图片时请注意数据安全和隐私保护

## 错误处理

函数包含完善的错误处理机制：
- 图片加载失败会返回相应错误信息
- 模型调用异常会有降级处理
- 网络超时会有重试机制

## 扩展功能

可以根据需要扩展以下功能：
1. 支持批量图片处理
2. 添加更多图像属性分析（色彩、构图等）
3. 集成更多视觉模型选择
4. 支持视频帧分析
