import os
import json
from typing import AsyncGenerator

import runpod

from deep_filter import deep_filter
from encryption_handler import EncryptionHandler

model_init_error = None

VERSION = "unknown"

try:
    with open("current_version.txt", "r") as f:
        VERSION = f.readline()

    encryption_key = os.getenv("ENCRYPTION_KEY")
    if encryption_key is None:
        encryption_handler = None
    else:
        encryption_handler = EncryptionHandler(encryption_key)

    from vllm import AsyncLLMEngine, SamplingParams
    from vllm.utils import random_uuid

    llm_parameters = os.getenv("VLLM_ENGINE_PARAMETERS")
    if llm_parameters is None:
        llm_parameters = "{}"

    model_name = os.getenv("VLLM_MODEL_NAME")
    llm = AsyncLLMEngine(model=model_name, **json.loads(llm_parameters))
except Exception as init_e:
    # Show to client when prompting
    model_init_error = init_e


async def handler(job) -> AsyncGenerator[any, None]:
    print("Processing with version", VERSION, "...")
    try:
        if model_init_error is not None:
            yield {'error': str(model_init_error), 'init': True}
            return

        job_input = job['input']
        prompt = job_input.get('prompt', False)

        if not prompt:
            yield {'error': 'Missing "prompt" key in input!'}
            return

        if encryption_handler is not None:
            prompt = encryption_handler.decrypt(prompt)

        request_id = random_uuid()
        sampling_params = job_input.get('parameters', {})
        generator = llm.generate(prompt, SamplingParams(**sampling_params), request_id)

        if job_input.get("streaming", False):
            async for async_request_output in generator:
                yield async_request_output
            return

        final_output = None
        async for request_output in generator:
            final_output = request_output

        output_filter = job_input.get('output_filter', [])
        filtered_output = deep_filter(final_output, output_filter)

        if encryption_handler is not None:
            yield encryption_handler.encrypt(json.dumps(filtered_output))
        else:
            yield filtered_output

    except Exception as e:
        yield {'error': str(e)}


runpod.serverless.start({"handler": handler, "return_aggregate_stream": True})
