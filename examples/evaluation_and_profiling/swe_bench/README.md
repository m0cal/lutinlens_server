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

# Solving problems in a SWE bench dataset using NeMo Agent Toolkit
This example provides a skeleton workflow which can be used to implement predictors to solve problems in a SWE bench dataset.

## Table of Contents

- [Key Features](#key-features)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
- [Quickstart](#quickstart)
- [Datasets](#datasets)
  - [Filtering dataset entries](#filtering-dataset-entries)
- [Predictors](#predictors)
  - [Adding a net new predictor](#adding-a-net-new-predictor)
- [Evaluation](#evaluation)
  - [Sample evaluation output](#sample-evaluation-output)

## Key Features

- **SWE-bench Dataset Integration:** Demonstrates how to use NeMo Agent toolkit with Software Engineering benchmark datasets including SWE-bench_Lite and SWE-bench_Verified for systematic code problem solving evaluation.
- **Docker-based Evaluation Environment:** Shows containerized evaluation setup ensuring consistent and isolated environments for running code modifications and testing solutions against benchmark problems.
- **Multi-Dataset Support:** Supports multiple SWE-bench dataset formats including JSON and Parquet files from HuggingFace datasets, with both local and remote dataset loading capabilities.
- **Configurable Problem Filtering:** Provides filtering mechanisms to limit dataset entries for focused evaluation and testing, enabling iterative development and debugging of solutions.
- **Pydantic Model Integration:** Uses structured `SWEBenchInput` data models for type-safe processing of software engineering problems with clear input/output specifications.

## Prerequisites

SWE bench evaluations run inside a Docker container.

Ensure that Docker is installed and the Docker service is running before proceeding.

- Install Docker: Follow the official installation guide for your platform: [Docker Installation Guide](https://docs.docker.com/engine/install/)
- Start Docker Service:
  - Linux: Run`sudo systemctl start docker` (ensure your user has permission to run Docker).
  - Mac & Windows: Docker Desktop should be running in the background.
- Verify Docker Installation: Run the following command to verify that Docker is installed and running correctly:
```bash
docker info
```

## Installation and Setup

If you have not already done so, follow the instructions in the [Install Guide](../../../docs/source/quick-start/installing.md#install-from-source)

### Install this Workflow

Install the `swe_bench` example:
```bash
uv pip install -e examples/evaluation_and_profiling/swe_bench
```

## Quickstart
Run the example via the `nat eval` CLI command:
```bash
nat eval --config_file examples/evaluation_and_profiling/swe_bench/configs/config_gold.yml
```

The configuration file specified above contains configurations for the NeMo Agent Toolkit `evaluation` and `profiler` capabilities. Additional documentation for evaluation configuration can be found in the [evaluation guide](../../../docs/source/workflows/evaluate.md). Furthermore, similar documentation for profiling configuration can be found in the [profiling guide](../../../docs/source/workflows/profiler.md).


## Datasets
This workflow requires the `swe_bench` dataset as a JSON or Parquet file. A few public datasets are provided in the data directory -
- data/dev_dataset_lite.json, downloaded from [SWE-bench_Lite](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite/viewer/default/dev)
- data/test_dataset_lite.json, downloaded from [SWE-bench_Lite](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite/viewer/default/test)
- data/test_dataset_verified.json, downloaded from [SWE-bench_Verified](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified)

And can be used to test the workflow by specifying the dataset in the configuration file:
```yaml
eval:
  general:
    dataset:
      _type: json
      file_path: examples/evaluation_and_profiling/swe_bench/data/test_dataset_lite.json
```

Alternately you can read any remote dataset by specifying the pandas URL in the configuration file:
```yaml
eval:
  dataset:
      _type: parquet
      file_path: hf://datasets/princeton-nlp/SWE-bench_Lite/data/test-00000-of-00001.parquet
```


The input to the workflow is a [Pydantic](https://docs.pydantic.dev) model, `SWEBenchInput`. Refer to `src/nat/data_models/swe_bench_model.py` for the model definition.

### Filtering dataset entries
You can limit the number of `swe_bench` instances in the dataset, that are solved and evaluated, via a filter in the configuration file. For example:
```yaml
eval:
  general:
    dataset:
      _type: json
      file_path: examples/evaluation_and_profiling/swe_bench/data/test_dataset_lite.json
      id_key: instance_id
      structure: # For swe-bench the entire row is the input
        disable: true
      filter:
        allowlist:
          field:
            instance_id:
              - sympy__sympy-20590
              - sympy__sympy-21055
```

This configuration runs the workflow and evaluation only on the two specified instances.

You can alternately filter out instances that are not to be solved and evaluated, via `eval.swe_bench.filter.denylist_instance_ids`. For example:
```yaml
eval:
  general:
    dataset:
      _type: json
      file_path: examples/evaluation_and_profiling/swe_bench/data/test_dataset_lite.json
      id_key: instance_id
      structure: # For swe-bench the entire row is the input
        disable: true
      filter:
        denylist:
          field:
            instance_id:
              - "astropy__astropy-6938"
              - "astropy__astropy-7746"
              - "psf__requests-2317"
              - "psf__requests-2674"
```
The configuration runs the workflow and evaluation on all instances in the dataset except the `denied` ones.

## Predictors
A predictor is a class that takes in a SWE bench input instance, solves the problem in the instance, and returns a patch.

The predictor uses the `repo`, `problem_statement` and `hints_text` in the `SWEBenchInput` instance to fix the bug in the code. It then returns the fix as a code patch.

The predictor should not use -
- the patch fields, `patch` and `test_patch` (or)
- the tests, `PASS_TO_PASS` and `FAIL_TO_PASS`
in the input instance.

That information is only used for evaluation. Using it can taint the predictor and lead to overfitting.

These predictors are provided in this NeMo Agent toolkit example:
- `gold` - Uses the patch from the `SWEBenchInput` instance, bypassing problem-solving logic. See [predict_gold_stub.py](src/nat_swe_bench/predictors/predict_gold/predict_gold_stub.py) and configuration file `examples/evaluation_and_profiling/swe_bench/configs/config_gold.yml`.
- `skeleton` - Skeleton code for creating a problem-solving workflow. This code can be copied to create a net-new predictor. See [predict_skeleton.py](src/nat_swe_bench/predictors/predict_skeleton/predict_skeleton.py) and configuration file `examples/evaluation_and_profiling/swe_bench/configs/config_skeleton.yml`.

### Adding a net new predictor
To add a new predictor:
- Create a new directory in the predictors directory, copy over the contents of [predictors/predict_skeleton](src/nat_swe_bench/predictors/predict_skeleton/). Rename the files and fill in the logic to solve the problem.
- Register the new predictor class with an unique name using the `@register_predictor` decorator.
- Import the new predictor class in [predictors/register.py](src/nat_swe_bench/predictors/register.py) to make it discoverable by the NeMo Agent toolkit `swe_bench` harness.

## Evaluation
The `model_patch` returned by the `swe_bench` workflow is run through the `swe_bench` evaluation harness. This harness -
- Launches a docker container with the `swe_bench` test image
- Installs the repo from the `SWEBenchInput` instance
- Applies the model patch in the `SWEBenchOutput`.
- Applies any test patch in the `SWEBenchInput` instance.
- Runs the `PASS_TO_PASS` and `FAIL_TO_PASS` tests in the `SWEBenchInput` instance
- Returns the evaluation results as a JSON report file with additional logs for troubleshooting.

The evaluation results, logs and reports, are stored in the output directory specified in the configuration file via `eval.general.output_dir`.



### Sample evaluation output
Run:
```bash
nat eval --config_file examples/evaluation_and_profiling/swe_bench/configs/config_gold.yml
```
Expected output:
```console
2025-07-31 19:39:37,616 - nat.eval.evaluate - INFO - Starting evaluation run with config file: examples/evaluation_and_profiling/swe_bench/configs/config_gold.yml
2025-07-31 19:39:38,764 - nat.runtime.loader - WARNING - Loading module 'nat_profiler_agent.register' from entry point 'nat_profiler_agent' took a long time (1084.733009 ms). Ensure all imports are inside your registered functions.
2025-07-31 19:39:39,160 - nat.runtime.loader - WARNING - Loading module 'nat_multi_frameworks.register' from entry point 'nat_multi_frameworks' took a long time (226.987600 ms). Ensure all imports are inside your registered functions.
2025-07-31 19:39:40,652 - nat.runtime.loader - WARNING - Loading module 'nat.agent.register' from entry point 'nat_agents' took a long time (1482.537985 ms). Ensure all imports are inside your registered functions.
2025-07-31 19:39:41,135 - nat.runtime.loader - WARNING - Loading module 'nat.experimental.inference_time_scaling.register' from entry point 'nat_inference_time_scaling' took a long time (266.962051 ms). Ensure all imports are inside your registered functions.
2025-07-31 19:39:41,430 - nat.runtime.loader - WARNING - Loading module 'nat.tool.register' from entry point 'nat_tools' took a long time (192.843914 ms). Ensure all imports are inside your registered functions.
2025-07-31 19:39:41,515 - nat.data_models.discovery_metadata - WARNING - Package metadata not found for simple_auth
2025-07-31 19:39:42,001 - nat.runtime.loader - WARNING - Loading module 'nat_alert_triage_agent.register' from entry point 'nat_alert_triage_agent' took a long time (457.817078 ms). Ensure all imports are inside your registered functions.
2025-07-31 19:39:42,179 - nat.runtime.loader - WARNING - Loading module 'nat_automated_description_generation.register' from entry point 'nat_automated_description_generation' took a long time (168.121815 ms). Ensure all imports are inside your registered functions.
2025-07-31 19:39:42,386 - nat.runtime.loader - WARNING - Loading module 'nat.plugins.agno.register' from entry point 'nat_agno' took a long time (206.707001 ms). Ensure all imports are inside your registered functions.
2025-07-31 19:39:43,111 - nat.runtime.loader - WARNING - Loading module 'nat.plugins.redis.register' from entry point 'nat_redis' took a long time (260.392904 ms). Ensure all imports are inside your registered functions.

<snipped for brevity>

Running workflow:   0%|                                                             | 0/2 [00:00<?, ?it/s]

<snipped for brevity>

2025-07-31 19:39:46,347 - nat.eval.swe_bench_evaluator.evaluate - INFO - Workflow input written to .tmp/nat/examples/evaluation_and_profiling/swe_bench/gold/nat_workflow_input.json
2025-07-31 19:39:46,352 - nat.eval.swe_bench_evaluator.evaluate - INFO - Workflow output written to .tmp/nat/examples/evaluation_and_profiling/swe_bench/gold/nat_workflow_output.json
2025-07-31 19:39:46,364 - nat.eval.swe_bench_evaluator.evaluate - INFO - Starting swe_bench run nat_1
Running 2 unevaluated instances...
Base image sweb.base.py.arm64:latest already exists, skipping build.
Base images built successfully.
No environment images need to be built.
Running 2 instances...
2 ran successfully, 0 failed: 100%|█████████████████████████████████████████████████| 2/2 [03:21<00:00, 201.41s/it]
All instances run.
Cleaning cached images...
Removed 0 images.
Total instances: 2
Instances submitted: 2
Instances completed: 2
Instances incomplete: 0
Instances resolved: 2
Instances unresolved: 0
Instances with empty patches: 0
Instances with errors: 0
Unstopped containers: 0
Unremoved images: 0
Report written to nv_predictor.nat_1.json
2025-07-31 19:40:44,591 - nat.eval.swe_bench_evaluator.evaluate - INFO - Completed swe_bench run nat_1
2025-07-31 19:40:44,592 - nat.eval.swe_bench_evaluator.evaluate - INFO - SWE_bench report and logs written to .tmp/nat/examples/evaluation_and_profiling/swe_bench/gold/swe_bench_reports directory
2025-07-31 19:40:44,596 - nat.eval.evaluate - INFO - Profiler is not enabled. Skipping profiling.
2025-07-31 19:40:44,600 - nat.eval.evaluate - INFO - Workflow output written to .tmp/nat/examples/evaluation_and_profiling/swe_bench/gold/workflow_output.json
2025-07-31 19:40:44,602 - nat.eval.evaluate - INFO - Evaluation results written to .tmp/nat/examples/evaluation_and_profiling/swe_bench/gold/swe_bench_output.json
```
