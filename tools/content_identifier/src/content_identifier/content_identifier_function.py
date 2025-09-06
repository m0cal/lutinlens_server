import logging
import base64
import requests
import os
from io import BytesIO
from PIL import Image
import numpy as np
from openai import OpenAI

from pydantic import Field

from .models.request import ContentIdentifyRequest
from .models.response import ContentIdentifyResponse

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)


class ContentIdentifierFunctionConfig(FunctionBaseConfig, name="content_identifier"):
    """
    Configuration for content identifier
    """
    api_key: str = Field(default_factory=lambda: os.getenv("DASHSCOPE_API_KEY", ""),
                        description="DashScope API key for accessing qwen-vl-max-latest model")
    base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1",
                         description="API base URL for DashScope service")
    model_name: str = Field(default="qwen-vl-max-latest",
                           description="Vision-language model name to use")




def determine_brightness_level(brightness_stats, content_analysis):
    """
    基于亮度统计和内容分析确定亮度级别
    """
    mean_brightness = brightness_stats['mean_brightness']
    dark_ratio = brightness_stats['dark_ratio']
    bright_ratio = brightness_stats['bright_ratio']

    # 检查是否为室外场景
    outdoor_keywords = ['天空', '云', '太阳', '户外', '街道', '建筑', '车辆', '树木', '公园']
    is_outdoor = any(keyword in content_analysis for keyword in outdoor_keywords)

    # 检查天气相关词汇
    sunny_keywords = ['阳光', '晴天', '明亮', '蓝天']
    cloudy_keywords = ['多云', '阴天', '云层']
    night_keywords = ['夜晚', '月亮', '星星', '路灯', '灯光']

    is_sunny = any(keyword in content_analysis for keyword in sunny_keywords)
    is_cloudy = any(keyword in content_analysis for keyword in cloudy_keywords)
    is_night = any(keyword in content_analysis for keyword in night_keywords)

    # 基于多个因素判断亮度
    if is_night or mean_brightness < 50:
        if dark_ratio > 0.7:
            return "非常昏暗 - 夜晚或极低光照环境，主要依靠人工照明"
        else:
            return "昏暗 - 夜晚环境下有适度的人工照明"

    elif mean_brightness < 80:
        if is_outdoor and is_cloudy:
            return "较暗 - 室外阴天环境，自然光照不足"
        elif not is_outdoor:
            return "较暗 - 室内环境，光照条件一般"
        else:
            return "较暗 - 光照条件不佳"

    elif mean_brightness < 120:
        if is_outdoor:
            if is_cloudy:
                return "中等亮度 - 室外多云天气，光照适中"
            else:
                return "中等亮度 - 室外环境，有适度的自然光照"
        else:
            return "中等亮度 - 室内有良好的人工或自然光照"

    elif mean_brightness < 180:
        if is_outdoor and is_sunny:
            return "明亮 - 室外晴天，阳光充足"
        elif is_outdoor:
            return "明亮 - 室外环境，光照良好"
        else:
            return "明亮 - 室内光照充足"

    else:
        if bright_ratio > 0.4:
            return "非常明亮 - 强烈阳光或高强度照明，可能存在过曝"
        else:
            return "非常明亮 - 优质的光照条件"


async def analyze_image_content_and_brightness(image_uri: str, config: ContentIdentifierFunctionConfig) -> tuple[str, str]:
    """使用视觉语言模型同时分析图像内容和亮度"""
    try:
        # 创建 OpenAI 客户端用于 DashScope API
        client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )

        # 构建消息，同时要求分析内容和亮度
        from typing import cast, Dict, Any, List

        messages = cast(List[Dict[str, Any]], [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """请分析这张图片，提供以下两部分信息：

1. 图片内容描述：详细描述图片的内容，包括场景、物体、人物、环境等所有可见元素。

2. 拍摄亮度评估：基于图片的视觉特征（如整体明暗程度、阴影、光照条件、室内外环境、天气状况等），判断拍摄时的亮度水平。请从以下选项中选择：
   - 非常亮（Strong Light）：强烈阳光或明亮室内照明
   - 较亮（Bright）：充足的自然光或良好室内照明
   - 适中（Moderate）：正常日光或一般室内照明
   - 较暗（Dim）：阴天、黄昏或昏暗室内
   - 很暗（Dark）：夜晚、严重阴天或极暗环境

请按照以下格式回答：
内容描述：[详细的图片内容描述]
亮度评估：[选择的亮度级别]"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_uri
                        }
                    }
                ]
            }
        ])

        # 调用API
        response = client.chat.completions.create(
            model=config.model_name,
            messages=messages,  # type: ignore
            max_tokens=1500,
            temperature=0.1
        )

        if response.choices and response.choices[0].message:
            content = response.choices[0].message.content

            # 解析回答，分离内容描述和亮度评估
            content_desc = ""
            brightness_desc = ""

            if content:
                lines = content.split('\n')
                current_section = None

                for line in lines:
                    line = line.strip()
                    if line.startswith('内容描述：'):
                        current_section = 'content'
                        content_desc = line.replace('内容描述：', '').strip()
                    elif line.startswith('亮度评估：'):
                        current_section = 'brightness'
                        brightness_desc = line.replace('亮度评估：', '').strip()
                    elif current_section == 'content' and line:
                        content_desc += f" {line}"
                    elif current_section == 'brightness' and line:
                        brightness_desc += f" {line}"

            # 如果解析失败，使用原始回答作为内容描述
            if not content_desc and content:
                content_desc = content
            if not brightness_desc:
                brightness_desc = "适中"

            return content_desc.strip() if content_desc else "无法分析图像内容", brightness_desc.strip()
        else:
            logger.error("No valid response from vision model")
            return "无法分析图像内容", "无法判断亮度级别"

    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return f"图像分析失败: {str(e)}", "无法判断亮度级别"
async def load_image_from_uri(image_uri: str):
    """
    从URI加载图像
    """
    try:
        if image_uri.startswith('http'):
            # 网络图片
            response = requests.get(image_uri, timeout=30)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
        elif image_uri.startswith('data:image'):
            # Base64编码的图片
            header, encoded = image_uri.split(',', 1)
            image_data = base64.b64decode(encoded)
            image = Image.open(BytesIO(image_data))
        else:
            # 本地文件路径
            image = Image.open(image_uri)

        # 转换为RGB模式
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # 转换为numpy数组
        image_array = np.array(image)

        return image_array

    except Exception as e:
        logger.error(f"Error loading image from URI: {e}")
        raise ValueError(f"Failed to load image: {str(e)}")


@register_function(config_type=ContentIdentifierFunctionConfig)
async def content_identifier_function(
    config: ContentIdentifierFunctionConfig, builder: Builder
):
    async def _response_fn(request: ContentIdentifyRequest) -> ContentIdentifyResponse:
        try:
            logger.info(f"Analyzing image: {request.image_uri}")

            # 使用视觉语言模型同时分析图像内容和亮度
            content_analysis, brightness_description = await analyze_image_content_and_brightness(
                request.image_uri,
                config
            )

            logger.info(f"Content analysis completed successfully")

            return ContentIdentifyResponse(
                content=content_analysis,
                brightness=brightness_description
            )

        except Exception as e:
            logger.error(f"Error in content identifier function: {e}")
            return ContentIdentifyResponse(
                content=f"图像内容分析失败: {str(e)}",
                brightness="无法判断亮度级别"
            )

    try:
        yield FunctionInfo.create(single_fn=_response_fn)
    except GeneratorExit:
        logger.warning("Function exited early!")
    finally:
        logger.info("Cleaning up content_identifier workflow.")
