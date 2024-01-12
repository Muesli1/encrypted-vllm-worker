import os
import json
from typing import AsyncGenerator

import runpod

from deep_filter import deep_filter, extract_single_value
from encryption_handler import EncryptionHandler

model_init_error = None

VERSION = "unknown"

try:
    import argparse
    from vllm import AsyncLLMEngine, AsyncEngineArgs, SamplingParams
    from vllm.utils import random_uuid


    def async_engine_args_from_dict(arg_dict: dict[str, any]) -> AsyncEngineArgs:
        parser = argparse.ArgumentParser()
        AsyncEngineArgs.add_cli_args(parser)

        combined_args = []

        for (key, value) in arg_dict.items():
            if value is False:
                # Ignore flag completely
                continue

            combined_args.append("--" + key)
            if value is True:
                # Nothing
                pass
            else:
                combined_args.append(str(value))

        parsed, unknown = parser.parse_known_args(combined_args)

        if len(unknown) > 0:
            raise ValueError("Unknown arguments: " + ", ".join(unknown) + "; Use:\n" + parser.format_help())

        return AsyncEngineArgs.from_cli_args(parsed)


    with open("current_version.txt", "r") as f:
        VERSION = f.readline()

    encryption_key = os.getenv("ENCRYPTION_KEY")
    if encryption_key is None:
        encryption_handler = None
    else:
        encryption_handler = EncryptionHandler(encryption_key)

    llm_parameters = os.getenv("VLLM_ENGINE_PARAMETERS")
    if llm_parameters is None:
        llm_parameters = "{}"

    model_name = os.getenv("VLLM_MODEL_NAME")
    llm = AsyncLLMEngine.from_engine_args(
        async_engine_args_from_dict({
            **json.loads(llm_parameters),
            "model": model_name
        })
    )
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

        streaming_minimize_traffic = job_input.get("'streaming_min_traffic", True)
        output_filter = job_input.get('output_filter', [])
        streaming_filter = job_input.get('streaming_filter', [])
        request_id = random_uuid()
        sampling_params = job_input.get('parameters', {})
        generator = llm.generate(prompt, SamplingParams(**sampling_params), request_id)

        final_output = None

        streaming = job_input.get("streaming", False)

        # Only stream changes instead of full text every time
        last_extracted = ""

        async for async_request_output in generator:
            final_output = async_request_output

            if streaming:
                filtered_async_output = deep_filter(async_request_output, streaming_filter)
                extracted_single_value = str(extract_single_value(filtered_async_output))
                partial_value = extracted_single_value

                if streaming_minimize_traffic and extracted_single_value.startswith(last_extracted):
                    partial_value = extracted_single_value[len(last_extracted):]
                last_extracted = extracted_single_value

                if encryption_handler is not None:
                    yield {'partial': encryption_handler.encrypt(partial_value)}
                else:
                    yield {'partial': partial_value}

        filtered_output = deep_filter(final_output, output_filter)

        if encryption_handler is not None:
            yield {'output': encryption_handler.encrypt(json.dumps(filtered_output))}
        else:
            yield {'output': filtered_output}

    except Exception as e:
        yield {'error': str(e)}


runpod.serverless.start({"handler": handler, "return_aggregate_stream": True})
