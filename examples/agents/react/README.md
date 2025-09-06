<!--
SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# ReAct Agent

A configurable ReAct agent. This agent leverages the NeMo Agent toolkit plugin system and `WorkflowBuilder` to integrate pre-built and custom tools into the workflow. Key elements are summarized below:

## Table of Contents

- [Key Features](#key-features)
- [Graph Structure](#graph-structure)
- [Installation and Setup](#installation-and-setup)
  - [Install this Workflow](#install-this-workflow)
  - [Set Up API Keys](#set-up-api-keys)
- [Run the Workflow](#run-the-workflow)
  - [Starting the NeMo Agent Toolkit Server](#starting-the-nemo-agent-toolkit-server)
  - [Making Requests to the NeMo Agent Toolkit Server](#making-requests-to-the-nemo-agent-toolkit-server)
  - [Evaluating the ReAct Agent Workflow](#evaluating-the-react-agent-workflow)

## Key Features

- **ReAct Agent Framework:** Demonstrates a `react_agent` that performs step-by-step reasoning between tool calls, utilizing tool names and descriptions to route appropriately to the correct tool.
- **Wikipedia Search Integration:** Shows integration with the `wikipedia_search` tool for retrieving factual information from Wikipedia sources.
- **Code Generation Capabilities:** Includes the `code_generation_tool` for generating code examples and technical content.
- **Dual-Node Graph Architecture:** Implements the characteristic ReAct pattern that alternates between reasoning (Agent Node) and tool execution (Tool Node) until reaching a final answer.
- **YAML-based Agent Configuration:** Fully configurable via YAML, allowing easy customization of tools, prompts, and agent behavior for different use cases.

## Graph Structure

The ReAct agent uses a dual-node graph architecture that alternates between reasoning and tool execution. The following diagram illustrates the agent's workflow:

<div align="center">
<img src="../../../docs/source/_static/dual_node_agent.png" alt="ReAct Agent Graph Structure" width="400" style="max-width: 100%; height: auto;">
</div>

**Workflow Overview:**
- **Start**: The agent begins processing with user input
- **Agent Node**: Performs reasoning and decides whether to use a tool or provide a final answer
- **Conditional Edge**: Routes the flow based on the agent's decision
- **Tool Node**: Executes the selected tool when needed
- **Cycle**: The agent can loop between reasoning and tool execution until it reaches a final answer

This architecture allows the ReAct agent to think step-by-step, use tools when necessary, and provide well-reasoned responses based on the available information.

## Installation and Setup

If you have not already done so, follow the instructions in the [Install Guide](../../../docs/source/quick-start/installing.md#install-from-source) to create the development environment and install NeMo Agent toolkit.

### Install this Workflow

From the root directory of the NeMo Agent toolkit library, run the following commands:

```bash
uv pip install -e .
```

The `code_generation` and `wiki_search` tools are part of the `nvidia-nat[langchain]` package.  To install the package run the following command:
```bash
# local package install from source
uv pip install -e '.[langchain]'
```

### Set Up API Keys
If you have not already done so, follow the [Obtaining API Keys](../../../docs/source/quick-start/installing.md#obtaining-api-keys) instructions to obtain an NVIDIA API key. You need to set your NVIDIA API key as an environment variable to access NVIDIA AI services:

```bash
export NVIDIA_API_KEY=<YOUR_API_KEY>
```

## Run the Workflow

The ReAct agent can be used as either a workflow or a function, and there's an example configuration that demonstrates both.
If you’re looking for an example workflow where the ReAct agent runs as the main workflow, refer to [config.yml](configs/config.yml).
To see the ReAct agent used as a function within a workflow, alongside the Reasoning Agent, refer to [config-reasoning.yml](configs/config-reasoning.yml).
This README primarily covers the former case, where the ReAct agent functions as the main workflow, in config.yml.
For more details, refer to the [ReAct agent documentation](../../../docs/source/workflows/about/react-agent.md) and the [Reasoning agent documentation](../../../docs/source/workflows/about/reasoning-agent.md)

Run the following command from the root of the NeMo Agent toolkit repo to execute this workflow with the specified input:

```bash
nat run --config_file=examples/agents/react/configs/config.yml --input "who was Djikstra?"
```

**Expected Workflow Output**
```console
<snipped for brevity>

[AGENT]
Calling tools: wikipedia_search
Tool's input: {"question": "Djikstra"}
Tool's response:
<Document source="https://en.wikipedia.org/wiki/Edsger_W._Dijkstra" page=""/>
Edsger Wybe Dijkstra ( DYKE-strə; Dutch: [ˈɛtsxər ˈʋibə ˈdɛikstraː] ; 11 May 1930 – 6 August 2002) was a Dutch computer scientist, programmer, software engineer, mathematician, and science essayist.
Born in Rotterdam in the Netherlands, Dijkstra studied mathematics and physics and then theoretical physics at the University of Leiden. Adriaan van Wijngaarden offered him a job as the first computer programmer in the Netherlands at the Mathematical Centre in Amsterdam, where he worked from 1952 until 1962. He formulated and solved the shortest path problem in 1956, and in 1960 developed the first compiler for the programming language ALGOL 60 in conjunction with colleague Jaap A. Zonneveld. In 1962 he moved to Eindhoven, and later to Nuenen, where he became a professor in the Mathematics Department at the Technische Hogeschool Eindhoven. In the late 1960s he built the THE multiprogramming system, which influence...
------------------------------
2025-04-23 14:59:26,159 - nat.agent.react_agent.agent - INFO -
------------------------------
[AGENT]
Agent input: who was Djikstra?
Agent's thoughts:
Thought: I now know the final answer

Final Answer: Edsger Wybe Dijkstra was a Dutch computer scientist, programmer, software engineer, mathematician, and science essayist who made significant contributions to the field of computer science, including formulating and solving the shortest path problem and developing the first compiler for the programming language ALGOL 60.
------------------------------
2025-04-23 14:59:26,164 - nat.front_ends.console.console_front_end_plugin - INFO -
--------------------------------------------------
Workflow Result:
['Edsger Wybe Dijkstra was a Dutch computer scientist, programmer, software engineer, mathematician, and science essayist who made significant contributions to the field of computer science, including formulating and solving the shortest path problem and developing the first compiler for the programming language ALGOL 60.']
```

### Starting the NeMo Agent Toolkit Server

You can start the NeMo Agent toolkit server using the `nat serve` command with the appropriate configuration file.

**Starting the ReAct Agent Example Workflow**

```bash
nat serve --config_file=examples/agents/react/configs/config.yml
```

### Making Requests to the NeMo Agent Toolkit Server

Once the server is running, you can make HTTP requests to interact with the workflow.

#### Non-Streaming Requests

**Non-Streaming Request to the ReAct Agent Example Workflow**

```bash
curl --request POST \
  --url http://localhost:8000/generate \
  --header 'Content-Type: application/json' \
  --data '{"input_message": "What are LLMs?"}'
```

#### Streaming Requests

**Streaming Request to the ReAct Agent Example Workflow**

```bash
curl --request POST \
  --url http://localhost:8000/generate/stream \
  --header 'Content-Type: application/json' \
  --data '{"input_message": "What are LLMs?"}'
```

### Evaluating the ReAct Agent Workflow
**Run and evaluate the `react_agent` example Workflow**

```bash
nat eval --config_file=examples/agents/react/configs/config.yml
```
