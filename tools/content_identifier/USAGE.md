# Content Identifier 使用指南

## 概述

content_identifier_function.py 已经成功实现，这是一个接受图片URI并使用自然语言输出图片整体内容和基于天气、室内外环境判断的拍摄亮度的工具。

## 主要功能

### 1. 图像内容分析
- 使用阿里云通义千问视觉语言模型 (qwen-vl-max-latest)
- 分析图像中的主要物体、场景、环境特征
- 识别室内外环境、天气状况
- 提供自然流畅的中文描述

### 2. 亮度判断
- 结合计算机视觉算法分析图像亮度统计
- 基于内容理解判断拍摄环境
- 综合评估得出亮度级别描述

## 快速开始

### 1. 设置环境变量
```bash
export DASHSCOPE_API_KEY="your_dashscope_api_key_here"
```

### 2. 运行测试
```bash
cd /home/mocal/nv2025hackathon/lutinlens_server/tools/content_identifier
python test_content_identifier.py
```

### 3. 作为服务运行
```bash
nat run --config example_config.yaml
```

然后发送请求：
```bash
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "image_uri": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"
  }'
```

## 文件结构

```
tools/content_identifier/
├── src/content_identifier/
│   ├── __init__.py
│   ├── content_identifier_function.py   # 主要功能实现
│   └── models/
│       ├── __init__.py
│       ├── request.py                   # 请求模型
│       └── response.py                  # 响应模型
├── test_content_identifier.py          # 测试脚本
├── example_config.yaml                 # 配置示例
└── README.md                           # 详细文档
```

## 技术特性

### API 集成
- 直接使用 OpenAI 客户端连接阿里云 DashScope API
- 支持 qwen-vl-max-latest 视觉语言模型
- 兼容 OpenAI API 格式

### 图像处理
- 支持多种图像来源：HTTP URL、Base64、本地文件
- 自动图像格式转换和预处理
- 亮度统计分析算法

### 错误处理
- 完善的异常捕获和错误处理
- 网络超时保护
- 降级处理机制

## 配置选项

### ContentIdentifierFunctionConfig
- `api_key`: DashScope API 密钥
- `base_url`: API 基础URL (默认: DashScope兼容模式)
- `model_name`: 模型名称 (默认: qwen-vl-max-latest)

## 示例输出

### 输入
```json
{
  "image_uri": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"
}
```

### 输出
```json
{
  "content": "这是一张温馨的室内照片，显示了一位年轻女孩和一只可爱的小狗。女孩坐在沙发上，怀里抱着一只小型犬，两者都显得非常放松和快乐。室内环境明亮温暖，可以看到自然光从窗户透进来，整体光照条件良好。",
  "brightness": "明亮 - 室内有良好的自然光照"
}
```

## 扩展能力

该工具可以轻松扩展支持：
- 其他视觉语言模型 (OpenAI GPT-4V, Claude等)
- 批量图片处理
- 更多图像属性分析
- 自定义亮度判断逻辑

## 注意事项

1. 确保有有效的 DASHSCOPE_API_KEY
2. 图片URL需要公开可访问
3. 注意API调用频率限制
4. 大图片可能需要更长处理时间
