import logging
import os
import json
from collections import deque
from typing import Dict, Deque, Tuple
from datetime import datetime, timedelta

from pydantic import Field
from openai import OpenAI

from .models.request import FramingRequest
from .models.response import FramingResponse

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)

# In-memory store for session data, storing (deque, last_access_time)
session_data: Dict[str, Tuple[Deque[Tuple[str, str]], datetime]] = {}
SESSION_TIMEOUT = timedelta(minutes=10)  # Sessions expire after 10 minutes of inactivity

def cleanup_expired_sessions():
    """Iterate through sessions and remove any that have expired."""
    now = datetime.now()
    expired_sessions = [
        sid for sid, (_, last_access) in session_data.items()
        if now - last_access > SESSION_TIMEOUT
    ]
    for sid in expired_sessions:
        del session_data[sid]
        logger.info(f"Cleaned up expired session: {sid}")

def get_session_queue(session_id: str, max_length: int) -> Deque[Tuple[str, str]]:
    """Get or create a session image queue, and update its last access time."""
    cleanup_expired_sessions()  # Periodically clean up old sessions
    if session_id not in session_data:
        session_data[session_id] = (deque(maxlen=max_length), datetime.now())
    else:
        # Update last access time on existing session
        queue, _ = session_data[session_id]
        session_data[session_id] = (queue, datetime.now())
    return session_data[session_id][0]


LLM_SYSTEM_PROMPT = """
你是专业摄影构图助手。
分析图片序列和历史建议，为最新图片提供一个简洁、可操作的构图调整指令。

- **分析**: 对比历史，评估最新图片的构图。
- **建议**: 若构图不佳，提供动词开头的操作指令 (如 "镜头向左移动"/"拍摄位置低一些"/"镜头离远一些"/"镜头向上转"/"镜头向右旋转"/"放大")，除此以外不要给予其他信息。
- **完成**: 若构图良好，建议为空。

**输出格式** (必须严格遵守的JSON):
{
  "ready_to_shoot": 0, // 0: 需调整, 1: 可拍摄
  "suggestion": "向左平移"
}
"""


class FramingAdvisorFunctionConfig(FunctionBaseConfig, name="framing_advisor"):
    """
    Configuration for the Framing Advisor function.
    """
    model_name: str = Field(default="qwen-vl-max-latest", description="The model to use for framing advice.")
    max_queue_length: int = Field(default=10, description="Maximum number of images to keep in session queue.")
    temperature: float = Field(default=0.1, description="Temperature for LLM generation (lower = more consistent).")
    max_tokens: int = Field(default=500, description="Maximum tokens for LLM response.")
    enable_detailed_logging: bool = Field(default=False, description="Enable detailed logging for debugging.")


@register_function(config_type=FramingAdvisorFunctionConfig)
async def framing_advisor_function(
    config: FramingAdvisorFunctionConfig, builder: Builder
):
    async def _response_fn(request: FramingRequest) -> FramingResponse:
        """
        Receives an image, adds it to a session queue with its suggestion, and returns framing advice from an LLM.
        """
        logger.info(f"Received framing request for session_id: {request.session_id}")

        image_queue = get_session_queue(request.session_id, config.max_queue_length)

        # --- 1. Prepare the content for the LLM based on history ---
        llm_content = []
        if not image_queue:
            # First request in the session
            llm_content.append({"type": "text", "text": "这是第一张图，请提供初始构图建议。"})
        else:
            # Subsequent requests, build the history
            llm_content.append({"type": "text", "text": "历史记录（图片-建议）如下，请为最新图片提供下一步指示。"})
            for i, (img_b64, suggestion) in enumerate(image_queue):
                llm_content.extend([
                    {"type": "image_url", "image_url": {"url": f"{img_b64}"}},
                    {"type": "text", "text": f"建议 {i+1}: '{suggestion or '无'}'"}
                ])

        # Add the current image for analysis
        llm_content.extend([
            {"type": "text", "text": "最新图片:"},
            {"type": "image_url", "image_url": {"url": f"{request.img}"}},
        ])

        # --- 2. Call the LLM ---
        try:
            dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
            if not dashscope_api_key:
                logger.error("DASHSCOPE_API_KEY environment variable is not set.")
                return FramingResponse(ready_to_shoot=0, suggestion="Server error: API key not configured.")

            client = OpenAI(api_key=dashscope_api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

            if config.enable_detailed_logging:
                logger.info(f"Sending {len(image_queue) + 1} images to LLM for analysis.")

            completion = client.chat.completions.create(
                model=config.model_name,
                messages=[
                    {"role": "system", "content": LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": llm_content},
                ],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )

            response_text = completion.choices[0].message.content
            if config.enable_detailed_logging:
                logger.info(f"LLM raw response: {response_text}")

            if not response_text:
                raise ValueError("LLM returned an empty response.")

            # --- 3. Parse the response and update history ---
            response_text = response_text.strip()
            json_str = response_text
            if json_str.startswith("```json"):
                json_str = json_str[7:-3].strip()
            elif json_str.startswith("```"):
                json_str = json_str.strip("```").strip()

            if not json_str.startswith("{"):
                start_idx = json_str.find("{")
                end_idx = json_str.rfind("}") + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = json_str[start_idx:end_idx]

            try:
                response_data = json.loads(json_str)
            except json.JSONDecodeError as parse_error:
                logger.error(f"Failed to parse JSON response: {parse_error}. Raw response: {response_text}")
                return FramingResponse(ready_to_shoot=0, suggestion="Error parsing LLM response.")

            new_suggestion = response_data.get("suggestion", "")

            # Add the new image and its corresponding suggestion to the queue for the next request
            image_queue.append((request.img, new_suggestion))

            return FramingResponse(
                ready_to_shoot=int(response_data.get("ready_to_shoot", 0)),
                suggestion=new_suggestion
            )

        except Exception as e:
            logger.error(f"Error calling LLM or processing response: {e}")
            return FramingResponse(ready_to_shoot=0, suggestion="Error processing the image.")

    try:
        yield FunctionInfo.create(single_fn=_response_fn)
    finally:
        logger.info("Cleaning up framing_advisor workflow.")
        session_data.clear() # Also clear all sessions on shutdown
