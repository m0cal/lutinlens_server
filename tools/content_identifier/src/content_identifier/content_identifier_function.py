import logging
import os
import requests
import base64
import mimetypes
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
                           description="Vision-language model name to se")


async def analyze_image_content_and_brightness(image_url: str, config: ContentIdentifierFunctionConfig) -> tuple[str, str]:
    """使用视觉语言模型同时分析图像内容和亮度"""
    try:
        # 下载图片
        logger.info(f"Downloading image from {image_url}")
        response = requests.get(image_url)
        response.raise_for_status()  # 如果下载失败则抛出异常
        image_data = response.content
        logger.info("Image downloaded successfully.")

        # 猜测MIME类型
        mime_type, _ = mimetypes.guess_type(image_url)
        if mime_type is None:
            # 如果从URL无法猜测，则从响应头中获取
            content_type = response.headers.get('Content-Type')
            if content_type:
                mime_type = content_type.split(';')[0]
            else:
                mime_type = "image/jpeg"  # 默认为jpeg
        logger.info(f"Guessed MIME type: {mime_type}")

        # 将图片编码为Base64
        base64_image = base64.b64encode(image_data).decode('utf-8')

        # 创建Data URI
        image_data_uri = f"data:{mime_type};base64,{base64_image}"

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
                            "url": image_data_uri
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

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading image: {e}")
        return f"图像下载失败: {str(e)}", "无法判断亮度级别"
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return f"图像分析失败: {str(e)}", "无法判断亮度级别"


@register_function(config_type=ContentIdentifierFunctionConfig)
async def content_identifier_function(
    config: ContentIdentifierFunctionConfig, builder: Builder
):
    async def _response_fn(request: ContentIdentifyRequest) -> ContentIdentifyResponse:
        try:
            logger.info(f"Analyzing image: {request.image_url}")

            # 使用视觉语言模型同时分析图像内容和亮度
            content_analysis, brightness_description = await analyze_image_content_and_brightness(
                request.image_url,
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
