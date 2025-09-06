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

from contextlib import asynccontextmanager

import pytest

from nat.builder.workflow_builder import WorkflowBuilder
from nat.plugins.s3.object_store import S3ObjectStoreClientConfig
from nat.test.object_store_tests import ObjectStoreTests

# NOTE: This test requires a local S3 server to be running.
# To launch a local server using docker, run the following command:
# docker run --rm -ti -p 9000:9000 -p 9001:9001 minio/minio:RELEASE.2025-07-18T21-56-31Z \
#     server /data --console-address ":9001"


@pytest.mark.integration
class TestS3ObjectStore(ObjectStoreTests):

    @asynccontextmanager
    async def _get_store(self):
        async with WorkflowBuilder() as builder:
            await builder.add_object_store(
                "object_store_name",
                S3ObjectStoreClientConfig(bucket_name="test",
                                          endpoint_url="http://localhost:9000",
                                          access_key="minioadmin",
                                          secret_key="minioadmin"))

            yield await builder.get_object_store_client("object_store_name")
