# lutinlens_server

A backend service for LutinLens, an AI camera app based on NeMo Agent Toolkit (NAT).

---
## Introduction

With NeMo Agent Toolkit, we created 3 workflows that are finally deployed as servers. Their methologies are introduced as follows.

1. **lut_advisor**

	Request with a photo url, response with a LUT ID suggestion.
	
	```mermaid
	sequenceDiagram
		participant User
		participant ContentIdentifier
		participant LUTFinder
		participant Agent
		
		User ->> Agent: Photo Url
		Agent ->> ContentIdentifier: Photo Url
		ContentIdentifier -->> Agent: Photo Content
		Agent ->> LUTFinder: Photo Content
		LUTFinder -->> Agent: LUT ID
		Agent -->> User: LUT ID
	```
2. **framing_advisor**
	
    Request with a session ID and a base64-encoded photo, response with an action as suggestion.
	```mermaid
	flowchart LR
		Photo --|SessionID|--> Context
		Context --> LLM
		LLM --> Action
	```
3. **s3**

	Object Storage.
   
## Deployment

1. `git clone` this repo.
2. Install NeMo with `https://docs.nvidia.com/nemo/agent-toolkit/1.2/quick-start/installing.html`
3. Install all tools under `tools/` as Python packages.
4. Use `nat serve` to deploy the workflows you want.
If you need to use S3 to provide photo storage for `lut_advisor`, edit `s3/s3.yml` according to your storage settings.
