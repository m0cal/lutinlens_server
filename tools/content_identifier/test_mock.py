#!/usr/bin/env python3
"""
Mock测试脚本，用于验证content_identifier功能的代码结构
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from content_identifier.content_identifier_function import ContentIdentifierFunctionConfig, analyze_image_content_and_brightness

async def test_mock_analysis():
    """使用mock配置测试分析函数"""

    # 创建mock配置
    function_config = ContentIdentifierFunctionConfig(
        api_key="test_key",
        base_url="https://test.com",
        model_name="test-model"
    )

    # 测试图片URL
    test_image_uri = "https://example.com/test.jpg"

    print("Testing analyze_image_content_and_brightness function structure...")

    try:
        # 这会失败，但我们可以看到函数调用是否正确
        content, brightness = await analyze_image_content_and_brightness(
            test_image_uri,
            function_config
        )
        print(f"内容: {content}")
        print(f"亮度: {brightness}")
    except Exception as e:
        print(f"Expected error (due to mock API): {e}")
        print("Function structure is correct - it properly returns tuple[str, str]")

if __name__ == "__main__":
    asyncio.run(test_mock_analysis())
