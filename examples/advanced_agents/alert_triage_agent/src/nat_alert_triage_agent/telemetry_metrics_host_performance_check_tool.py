# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import statistics
from datetime import UTC
from datetime import datetime
from datetime import timedelta

import requests
from pydantic import Field

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.component_ref import LLMRef
from nat.data_models.function import FunctionBaseConfig

from . import utils
from .prompts import TelemetryMetricsHostPerformanceCheckPrompts


class TelemetryMetricsHostPerformanceCheckToolConfig(FunctionBaseConfig,
                                                     name="telemetry_metrics_host_performance_check"):
    description: str = Field(default=TelemetryMetricsHostPerformanceCheckPrompts.TOOL_DESCRIPTION,
                             description="Description of the tool.")
    llm_name: LLMRef
    prompt: str = Field(default=TelemetryMetricsHostPerformanceCheckPrompts.PROMPT,
                        description="Main prompt for the telemetry metrics host performance check task.")
    offline_mode: bool = Field(default=True, description="Whether to run in offline model")
    metrics_url: str = Field(default="", description="URL of the monitoring system")


def _timeseries_stats(ts):
    """Calculate and format summary statistics for a time series.

    Args:
        ts (list): List of numeric values representing a time series

    Returns:
        str: Markdown formatted string containing summary statistics
    """
    if len(ts) == 0:
        return "No data points"

    count = len(ts)
    max_val = max(ts)
    min_val = min(ts)
    mean_val = sum(ts) / count if count > 0 else float("nan")
    median_val = statistics.median(ts)

    markdown_summary = f"""
Time Series Statistics
- Number of Data Points: {count}
- Maximum Value: {max_val}
- Minimum Value: {min_val}
- Mean Value: {mean_val:.2f}
- Median Value: {median_val}
"""
    return markdown_summary


def _get_llm_analysis_input(timestamp_value_list):
    """Format telemetry metric data for LLM analysis.

    Takes raw telemetry metric data and formats it into a string containing:
    1. A timestamp-value timeseries in JSON format
    2. Summary statistics of the values

    The input timestamp_value_list is expected to be a list of [timestamp, value] pairs, where:
    - timestamp is a Unix timestamp (seconds since epoch)
    - value is a numeric string or number representing the metric value

    Example input:
    [[1642435200, "45.2"], [1642438800, "47.8"], ...]

    Args:
        timestamp_value_list (list): List of [timestamp, value] pairs from telemetry data

    Returns:
        str: Formatted string containing:
            - JSON array of [datetime_str, value] pairs with human readable timestamps
            - Summary statistics of the metric values
            - "No data points" if input list is empty
    """
    if len(timestamp_value_list) == 0:
        return "No data points"

    # Convert Unix timestamps to ISO format datetime strings and preserve values
    # Example: "2022-01-17 12:00:00" for timestamp 1642435200
    data = [[datetime.fromtimestamp(entry[0]).strftime("%Y-%m-%d %H:%M:%S"), entry[1]]
            for entry in timestamp_value_list]

    # Extract metric values and convert to float for statistical analysis
    # Assumes values are numeric strings or numbers
    ts = [float(entry[1]) for entry in timestamp_value_list]

    # Format data for LLM analysis by combining:
    # 1. The full timeseries as JSON
    # 2. Statistical summary from _timeseries_stats()
    input_str = f"""Timeseries:\n{json.dumps(data)}\n\n{_timeseries_stats(ts)}"""
    return input_str


@register_function(config_type=TelemetryMetricsHostPerformanceCheckToolConfig)
async def telemetry_metrics_host_performance_check_tool(config: TelemetryMetricsHostPerformanceCheckToolConfig,
                                                        builder: Builder):

    async def _arun(host_id: str) -> str:
        utils.log_header("Telemetry Metrics CPU Usage Pattern Analysis", dash_length=100)

        try:
            if not config.offline_mode:
                # Example implementation using a monitoring system's API to check host status
                monitoring_url = config.metrics_url

                # Customize query based on your monitoring setup and metrics
                # This example queries the CPU usage percentage by subtracting idle CPU from 100%
                query = f'(100 - cpu_usage_idle{{cpu="cpu-total",instance=~"{host_id}:9100"}})'
                url = f"{monitoring_url}/api/query_range"

                # Example values - users should customize these based on their monitoring requirements
                step = "30m"  # Adjust granularity of data points
                end_time = datetime.now(UTC)  # Current time as end point
                start_time = end_time - timedelta(weeks=2)  # Look back 2 weeks

                start_time_str = start_time.isoformat()
                end_time_str = end_time.isoformat()
                params = {"query": query, "start": start_time_str, "end": end_time_str, "step": step}

                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

            else:
                # In offline model, load offline data from CSV file
                df = utils.get_offline_data()
                data_str = utils.load_column_or_static(
                    df=df,
                    host_id=host_id,
                    column="telemetry_metrics_host_performance_check_tool:performance_check_output")
                data = json.loads(data_str)

            # Extract the timestamp-value timeseries from the response
            data = data["data"]["result"][0]["values"]

            # Additional LLM reasoning layer on playbook output to provide a summary of the results
            utils.log_header("LLM Reasoning", dash_length=30)

            data_input = _get_llm_analysis_input(data)
            conclusion = await utils.llm_ainvoke(
                config,
                builder,
                user_prompt=data_input,
                system_prompt=config.prompt,
            )
            utils.logger.debug(conclusion)
            utils.log_footer(dash_length=50)
            return conclusion

        except Exception as e:
            utils.logger.error("Error during telemetry metrics host performance check: %s", str(e))
            raise e

    yield FunctionInfo.from_fn(
        _arun,
        description=config.description,
    )
