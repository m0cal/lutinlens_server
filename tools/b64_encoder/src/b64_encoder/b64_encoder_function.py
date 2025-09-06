import logging
import base64

from pydantic import Field

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)


class B64EncoderFunctionConfig(FunctionBaseConfig, name="b64_encoder"):
    """
    Encodes a string to base64.
    """
    pass


@register_function(config_type=B64EncoderFunctionConfig)
async def b64_encoder_function(
    config: B64EncoderFunctionConfig, builder: Builder
):
    """
    This function takes a string as input and returns its base64 encoded representation.
    """
    async def _response_fn(input_message: str) -> str:
        # Process the input_message and generate output
        logger.info(f"Received input for base64 encoding.")
        input_bytes = input_message.encode('utf-8')
        encoded_bytes = base64.b64encode(input_bytes)
        output_message = encoded_bytes.decode('utf-8')
        logger.info(f"Base64 encoded output generated.")
        return output_message

    try:
        yield FunctionInfo.create(single_fn=_response_fn)
    except GeneratorExit:
        logger.warning("Function exited early!")
    finally:
        logger.info("Cleaning up b64_encoder workflow.")
