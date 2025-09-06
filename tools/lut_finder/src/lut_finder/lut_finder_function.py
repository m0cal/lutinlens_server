import logging
import os
from openai import OpenAI
from pathlib import Path
from typing import Any

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)


class LutFinderFunctionConfig(FunctionBaseConfig, name="lut_finder"):
    """
    Finds the best LUT for a given image description using an LLM.
    """
    pass


@register_function(config_type=LutFinderFunctionConfig)
async def lut_finder_function(
    config: LutFinderFunctionConfig, builder: Builder
):
    """
    This function takes a description of an image and uses an LLM to select the most
    appropriate LUT from a local directory, returning the filename of the selected LUT file.
    """
    # Path to the directory where LUTs are stored.
    # Assumes a 'luts' directory at the same level as the 'src' directory.
    luts_dir = Path(__file__).parent.parent.parent / "luts"

    # Initialize the OpenAI client to connect to Dashscope
    try:
        client = OpenAI(
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client for Dashscope: {e}")
        raise

    async def _response_fn(description: str) -> str:
        """
        Finds the best LUT for the given description and returns its filename.
        """
        try:
            lut_files = [f for f in os.listdir(luts_dir) if f.endswith('.cube')]
            if not lut_files:
                return "Error: No LUT files found in the specified directory."

            lut_names = [os.path.splitext(f)[0] for f in lut_files]

            prompt = (
                f"You are an expert in color grading. Based on the following image description, "
                f"which of the available LUTs would be most suitable? "
                f"Please return only the name of the best LUT from the list.\n\n"
                f"Image Description: '{description}'\n\n"
                f"Available LUTs: {', '.join(lut_names)}"
            )

            logger.info("Asking LLM to choose the best LUT...")
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="qwen-plus",
            )

            if not chat_completion.choices or not chat_completion.choices[0].message.content:
                return "Error: LLM did not return a valid response."

            chosen_lut_name = chat_completion.choices[0].message.content.strip()
            logger.info(f"LLM chose: {chosen_lut_name}")

            # Find the corresponding file, allowing for some flexibility in the LLM's response
            chosen_file = None
            for f in lut_files:
                if os.path.splitext(f)[0].lower() == chosen_lut_name.lower():
                    chosen_file = f
                    break

            if not chosen_file:
                 return f"Error: LLM returned a LUT name ('{chosen_lut_name}') that does not match any available files."

            return chosen_file

        except Exception as e:
            logger.error(f"An error occurred in lut_finder: {e}")
            return f"Error: An unexpected error occurred while finding the LUT. {e}"

    try:
        yield FunctionInfo.create(single_fn=_response_fn)
    except GeneratorExit:
        logger.warning("Function exited early!")
    finally:
        logger.info("Cleaning up lut_finder workflow.")


def __call__(self, **kwargs: Any) -> Any:
        """
        Finds a LUT file based on the provided image content.

        Args:
            **kwargs (Any): The input to the function, matching the Input model.

        Returns:
            str: The filename of the found LUT file.
        """
        # 1. 搜索合适的LUT
        image_content = kwargs.get("image_content", "")
        lut_filename = self._vector_store.search(image_content)
        if not lut_filename:
            return "No suitable LUT found."

        return lut_filename
