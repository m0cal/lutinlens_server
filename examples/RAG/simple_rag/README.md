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


# Simple RAG Example
This is a simple example RAG application to showcase how one can configure and use the  Retriever component. This example includes:
 - The config file to run the workflow
 - A docker compose deployment for standing up Milvus
 - A script for scraping data from URLs and storing it in Milvus

 This example is intended to be illustrative and demonstrate how someone could build a simple RAG application using the retriever component and use it with an agent without any additional code required!

## Table of Contents

- [Key Features](#key-features)
- [Quickstart: RAG with Milvus](#quickstart-rag-with-milvus)
  - [Installation and Setup](#installation-and-setup)
    - [Install this Workflow](#install-this-workflow)
    - [Set Up Milvus](#set-up-milvus)
    - [Set Up API Keys](#set-up-api-keys)
    - [Bootstrap Data](#bootstrap-data)
    - [Configure Your Agent](#configure-your-agent)
    - [Run the Workflow](#run-the-workflow)
- [Adding Long-Term Agent Memory](#adding-long-term-agent-memory)
  - [Prerequisites](#prerequisites)
  - [Adding Memory to the Agent](#adding-memory-to-the-agent)
- [Adding Additional Tools](#adding-additional-tools)
- [Using Test Time Compute](#using-test-time-compute)

## Key Features

- **Milvus Vector Database Integration:** Demonstrates the `milvus_retriever` component for storing and retrieving document embeddings from CUDA and MCP documentation.
- **ReAct Agent with RAG:** Shows how a `react_agent` can use retriever tools to answer questions by searching through indexed documentation.
- **Long-term Memory with Mem0:** Includes integration with Mem0 platform for persistent memory, allowing the agent to remember user preferences across sessions.
- **Multi-Collection Retrieval:** Demonstrates multiple retriever tools (`cuda_retriever_tool` and `mcp_retriever_tool`) for searching different knowledge bases.
- **Additional Tool Integration:** Shows how to extend the RAG system with complementary tools like `tavily_internet_search` and `code_generation` for comprehensive question answering.

## Quickstart: RAG with Milvus

### Installation and Setup

If you have not already done so, follow the instructions in the [Install Guide](../../../docs/source/quick-start/installing.md#install-from-source) to create the development environment and install NeMo Agent toolkit, and follow the [Obtaining API Keys](../../../docs/source/quick-start/installing.md#obtaining-api-keys) instructions to obtain an NVIDIA API key.

#### Install this Workflow

From the root directory of the NeMo Agent toolkit library, run the following commands:
```bash
uv pip install -e examples/RAG/simple_rag
```

#### Set Up Milvus

Start the docker compose [Skip this step if you already have Milvus running]
```bash
docker compose -f examples/RAG/simple_rag/deploy/docker-compose.yaml up -d
```
> Note: It can take some time for Milvus to start up. You can check the logs with:
```bash
docker compose -f examples/RAG/simple_rag/deploy/docker-compose.yaml logs --follow
```

#### Set Up API Keys

Export your NVIDIA API key:
```bash
export NVIDIA_API_KEY=<YOUR API KEY HERE>
```

#### Bootstrap Data

In a new terminal, from the root of the NeMo Agent toolkit repository, run the provided bash script to store the data in a Milvus collection. By default the script will scrape a few pages from the CUDA documentation and store the data in a Milvus collection called `cuda_docs`. It will also pull a few pages of information about the Model Context Protocol (MCP) and store it in a collection called `mcp_docs`.

```bash
source .venv/bin/activate
scripts/bootstrap_milvus.sh
```

If Milvus is running the script should work out of the box. If you want to customize the script the arguments are shown below.
```bash
python scripts/langchain_web_ingest.py --help
```
```console
usage: langchain_web_ingest.py [-h] [--urls URLS] [--collection_name COLLECTION_NAME] [--milvus_uri MILVUS_URI] [--clean_cache]

options:
-h, --help            show this help message and exit
--urls URLS           Urls to scrape for RAG context (default: ['https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html',
                                                                'https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html',
                                                                'https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html',
                                                                'https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/index.html'])
--collection_name COLLECTION_NAME, -n COLLECTION_NAME
                        Collection name for the data. (default: cuda_docs)
--milvus_uri MILVUS_URI, -u MILVUS_URI
                        Milvus host URI (default: http://localhost:19530)
--clean_cache         If true, deletes local files (default: False)
```

#### Configure Your Agent

Configure your Agent to use the Milvus collections for RAG. We have pre-configured a configuration file for you in `examples/RAG/simple_rag/configs/milvus_rag_config.yml`. You can modify this file to point to your Milvus instance and collections or add tools to your agent. The agent, by default, is a `tool_calling` agent that can be used to interact with the retriever component. The configuration file is shown below. You can also modify your agent to be another one of the NeMo Agent toolkit pre-built agent implementations such as the `react_agent`

    ```yaml
    general:
      use_uvloop: true

    retrievers:
      cuda_retriever:
        _type: milvus_retriever
        uri: http://localhost:19530
        collection_name: "cuda_docs"
        embedding_model: milvus_embedder
        top_k: 10
      mcp_retriever:
        _type: milvus_retriever
        uri: http://localhost:19530
        collection_name: "mcp_docs"
        embedding_model: milvus_embedder
        top_k: 10

    functions:
      cuda_retriever_tool:
        _type: nat_retriever
        retriever: cuda_retriever
        topic: Retrieve documentation for NVIDIA's CUDA library
      mcp_retriever_tool:
        _type: nat_retriever
        retriever: mcp_retriever
        topic: Retrieve information about Model Context Protocol (MCP)

    llms:
      nim_llm:
        _type: nim
        model_name: meta/llama-3.3-70b-instruct
        temperature: 0
        max_tokens: 4096
        top_p: 1

    embedders:
      milvus_embedder:
        _type: nim
        model_name: nvidia/nv-embedqa-e5-v5
        truncate: "END"

    workflow:
      _type: react_agent
      tool_names:
       - cuda_retriever_tool
         - mcp_retriever_tool
      verbose: true
      llm_name: nim_llm
    ```

    If you have a different Milvus instance or collection names, you can modify the `retrievers` section of the config file to point to your instance and collections. You can also add additional functions as tools for your agent in the `functions` section.

#### Run the Workflow

```bash
nat run --config_file examples/RAG/simple_rag/configs/milvus_rag_config.yml --input "How do I install CUDA"
```

The expected workflow result of running the above command is:
```console
['To install CUDA, you typically need to: \n1. Verify you have a CUDA-capable GPU and a supported version of your operating system.\n2. Download the NVIDIA CUDA Toolkit from the official NVIDIA website.\n3. Choose an installation method, such as a local repository installation or a network repository installation, depending on your system.\n4. Follow the specific instructions for your operating system, which may include installing local repository packages, enabling network repositories, or running installer scripts.\n5. Reboot your system and perform post-installation actions, such as setting up your environment and verifying the installation by running sample projects. \n\nPlease refer to the official NVIDIA CUDA documentation for detailed instructions tailored to your specific operating system and distribution.']
```

## Adding Long-Term Agent Memory
If you want to add long-term memory to your agent, you can do so by adding a `memory` section to your configuration file. The memory section is used to store information that the agent can use to provide more contextually relevant answers to the user's questions. The memory section can be used to store information such as user preferences, past interactions, or any other information that the agent needs to remember.

### Prerequisites
This section requires an API key for integration with the Mem0 Platform. To create an API key, refer to the instructions in the [Mem0 Platform Guide](https://docs.mem0.ai/platform/quickstart). Once you have created your API key, export it as an environment variable:
```bash
export MEM0_API_KEY=<MEM0 API KEY HERE>
```

### Adding Memory to the Agent
Adding the ability to add and retrieve long-term memory to the agent is just a matter of adding a `memory` section to the configuration file. The NeMo Agent toolkit built-in abstractions for long term memory management allow agents to automatically interact with them as tools. We will use the following configuration file, which you can also find in the `configs` directory.

```yaml
general:
  use_uvloop: true

memory:
  saas_memory:
    _type: mem0_memory

retrievers:
  cuda_retriever:
    _type: milvus_retriever
    uri: http://localhost:19530
    collection_name: "cuda_docs"
    embedding_model: milvus_embedder
    top_k: 10
  mcp_retriever:
    _type: milvus_retriever
    uri: http://localhost:19530
    collection_name: "mcp_docs"
    embedding_model: milvus_embedder
    top_k: 10

functions:
  cuda_retriever_tool:
    _type: nat_retriever
    retriever: cuda_retriever
    topic: Retrieve documentation for NVIDIA's CUDA library
  mcp_retriever_tool:
    _type: nat_retriever
    retriever: mcp_retriever
    topic: Retrieve information about Model Context Protocol (MCP)
  add_memory:
    _type: add_memory
    memory: saas_memory
    description: |
      Add any facts about user preferences to long term memory. Always use this if users mention a preference.
      The input to this tool should be a string that describes the user's preference, not the question or answer.
  get_memory:
    _type: get_memory
    memory: saas_memory
    description: |
      Always call this tool before calling any other tools, even if the user does not mention to use it.
      The question should be about user preferences which will help you format your response.
      For example: "How does the user like responses formatted?"

llms:
  nim_llm:
    _type: nim
    model_name: meta/llama-3.3-70b-instruct
    temperature: 0
    max_tokens: 4096
    top_p: 1

embedders:
  milvus_embedder:
    _type: nim
    model_name: nvidia/nv-embedqa-e5-v5
    truncate: "END"

workflow:
  _type: react_agent
  tool_names:
   - cuda_retriever_tool
   - mcp_retriever_tool
   - add_memory
   - get_memory
  verbose: true
  llm_name: nim_llm
```

Notice in the configuration above that the only addition to the configuration that was required to add long term memory to the agent was a `memory` section in the configuration specifying:
- The type of memory to use (`mem0_memory`)
- The name of the memory (`saas_memory`)

Then, we used native NeMo Agent toolkit functions for getting memory and adding memory to the agent. These functions are:
- `add_memory`: This function is used to add any facts about user preferences to long term memory.
- `get_memory`: This function is used to retrieve any facts about user preferences from long term memory.

Each function was given a description that helps the agent know when to use it as a tool. With the configuration in place, we can run the workflow again.
This time, we will tell the agent about how we like our responses formatted, and notice if it stores that fact to long term memory.

```bash
nat run --config_file=examples/RAG/simple_rag/configs/milvus_memory_rag_config.yml --input "How do I install CUDA? I like responses with a lot of emojis in them! :)"
```

The expected workflow result of the above run is:

```console
['🎉 To install CUDA, you can follow these steps: \n1. Verify you have a CUDA-capable GPU 🖥️ and a supported version of Linux 🐧.\n2. Download the NVIDIA CUDA Toolkit from https://developer.nvidia.com/cuda-downloads 📦.\n3. Choose an installation method: distribution-specific packages (RPM and Deb packages) or a distribution-independent package (runfile packages) 📈.\n4. Install the CUDA SDK using the chosen method, such as `dnf install cuda-toolkit` for Fedora 📊.\n5. Reboot the system 🔄.\n6. Perform post-installation actions, such as setting up the environment and verifying the installation 🎊.\nRemember to check the CUDA Installation Guide for Linux for more detailed instructions and specific requirements for your system 📚. 🎉']
```

We see from the above output that the agent was able to successfully retrieve our preference for emoji's in responses from long term memory and use it to format the response to our question about installing CUDA.

In this way, you can easily construct an agent that answers questions about your knowledge base and stores long term memories, all without any agent code required!

Note: The long-term memory feature relies on LLM-based tool invocation, which can occasionally be non-deterministic. If you notice that the memory functionality isn't working as expected (e.g., the agent doesn't remember your preferences), simply re-run your first and second inputs. This will help ensure the memory tools are properly invoked and your preferences are correctly stored.

## Adding Additional Tools
This workflow can be further enhanced by adding additional tools. Included with this example are two additional tools: `tavily_internet_search` and `code_generation`.

Prior to using the `tavily_internet_search` tool, create an account at [`tavily.com`](https://tavily.com/) and obtain an API key. Once obtained, set the `TAVILY_API_KEY` environment variable to the API key:
```bash
export TAVILY_API_KEY=<YOUR_TAVILY_API_KEY>
```
or update the workflow config file to include the `api_key`.

These workflows demonstrate how agents can use multiple tools in tandem to provide more robust responses. Both `milvus_memory_rag_tools_config.yml` and `milvus_rag_tools_config.yml` use these additional tools.

We can now run one of these workflows with a slightly more complex input.

```bash
nat run --config_file examples/RAG/simple_rag/configs/milvus_rag_tools_config.yml --input "How do I install CUDA and get started developing with it? Provide example python code"
```
The expected workflow result of the above run is:
```console
["To install CUDA and get started with developing applications using it, you can follow the instructions provided in the CUDA Installation Guide for your specific operating system. The guide covers various installation methods, including package manager installation, runfile installation, Conda installation, and pip wheels. After installing CUDA, you can use it in your Python applications by importing the cupy library, which provides a similar interface to numpy but uses the GPU for computations. Here's an example Python code that demonstrates how to use CUDA:\n\n```python\nimport numpy as np\nimport cupy as cp\n\n# Create a sample array\narr = np.array([1, 2, 3, 4, 5])\n\n# Transfer the array to the GPU\narr_gpu = cp.asarray(arr)\n\n# Perform some operations on the GPU\nresult_gpu = cp.square(arr_gpu)\n\n# Transfer the result back to the CPU\nresult_cpu = cp.asnumpy(result_gpu)\n\nprint(result_cpu)\n```\n\nThis code creates a sample array, transfers it to the GPU, performs a square operation on the GPU, and then transfers the result back to the CPU for printing. Make sure to install the cupy library and have a CUDA-capable GPU to run this code."]
```

## Using Test Time Compute
You can also use the experimental `test_time_compute` feature to scale the inference time of the agent. Particularly, in this example, we demonstrate how to enable multiple
executions of the retrieval agent with a higher LLM temperature to encourage diversity. We then merge the outputs of the multiple runs with another LLM call to synthesize one comprehensive answer from multiple searches.

An example configuration can be found in the `configs/milvus_rag_config_ttc.yml` file. Notably, it has a few additions to the standard configuration:
- An `ttc_strategies` section of the configuration that details which Test Time Compute techniques will be used in the workflow
- A `selection_strategy` called `llm_based_agent_output_merging` selection, that takes the output of multiple workflow runs and combines them using a single LLM call.
- A new `workflow` entrypoint called the `execute_score_select` function. The function executes the `augmented_fn` (the ReAct agent here) `num_iterations` times, and then passes the outputs to the selector.

To run this workflow, you can use the following command:
```bash
nat run --config_file examples/RAG/simple_rag/configs/milvus_rag_config_ttc.yml --input "What is the difference between CUDA and MCP?"
```

You should see several concurrent agent runs in the intermediate output which include output similar to:
```console
[AGENT]
Agent input: What is the difference between CUDA and MCP?
Agent's thoughts:
Thought: I now know what MCP is. It is the Model Context Protocol, which is a protocol that allows Large Language Models (LLMs) to securely access tools and data sources.

To answer the question, I will compare CUDA and MCP.

CUDA is a parallel computing platform and programming model developed by NVIDIA, while MCP is a protocol for LLMs to access tools and data sources.

The main difference between CUDA and MCP is their purpose and application. CUDA is primarily used for general-purpose parallel computing, while MCP is specifically designed for LLMs to access external tools and data sources.

Final Answer: The main difference between CUDA and MCP is that CUDA is a parallel computing platform and programming model, while MCP is a protocol that allows Large Language Models (LLMs) to securely access tools and data sources.
```

You may also see that one of the workflow runs "fails" with the following error. You can ignore the error if present as it can happen due to the nature of LLMs.

```console
[AGENT]
Agent input: What is the difference between CUDA and MCP?
Agent's thoughts:
Thought: I have found information about CUDA and MCP. CUDA is a general-purpose parallel computing platform and programming model developed by NVIDIA, while MCP stands for Model Context Protocol, which is a protocol that enables large language models (LLMs) to securely access tools and data sources.

Action: None
```

Near the end of the output you should see the following lines indicating that the Test Time Compute feature is working as expected.
```console
2025-07-31 15:01:06,939 - nat.experimental.test_time_compute.functions.execute_score_select_function - INFO - Beginning selection
2025-07-31 15:01:08,633 - nat.experimental.test_time_compute.selection.llm_based_output_merging_selector - INFO - Merged output: The main difference between CUDA and MCP is their purpose and scope. CUDA is a general-purpose parallel computing platform and programming model developed by NVIDIA, while MCP stands for Model Context Protocol, which is a protocol that enables large language models (LLMs) to securely access tools and data sources. In essence, CUDA is designed for parallel computing and programming, whereas MCP is specifically designed to facilitate secure access to tools and data sources for Large Language Models. This distinction highlights the unique objectives and applications of each technology, with CUDA focusing on computation and MCP focusing on secure data access for AI models.
```

The final workflow result should look similar to the following:
```console
['CUDA and MCP are two distinct technologies with different purposes and cannot be directly compared. CUDA is a parallel computing platform and programming model, primarily used for compute-intensive tasks such as scientific simulations, data analytics, and machine learning, whereas MCP is an open protocol designed for providing context to Large Language Models (LLMs), particularly for natural language processing and other AI-related tasks. While they serve different purposes, CUDA and MCP share a common goal of enabling developers to create powerful and efficient applications. They are complementary technologies that can be utilized together in certain applications to achieve innovative outcomes, although their differences in design and functionality set them apart. In essence, CUDA focuses on parallel computing and is developed by NVIDIA, whereas MCP is focused on context provision for LLMs, making them unique in their respective fields but potentially synergistic in specific use cases.']
```
