import os
import json

import runpod

from deep_filter import deep_filter

model_init_error = None

try:
    from vllm import LLM, SamplingParams

    llm_parameters = os.getenv("VLLM_ENGINE_PARAMETERS")
    if llm_parameters is None:
        llm_parameters = "{}"

    model_name = os.getenv("VLLM_MODEL_NAME")
    llm = LLM(model=model_name, **json.loads(llm_parameters))
except Exception as init_e:
    # Show to client when prompting
    model_init_error = init_e


def handler(job):
    try:
        if model_init_error is not None:
            return {'error': str(model_init_error), 'init': True}

        job_input = job['input']

        prompt = job_input.get('prompt', False)
        sampling_params = job_input.get('parameters', {})

        if not prompt:
            return {'error': 'Missing "prompt" key in input!'}

        outputs = llm.generate(prompt, SamplingParams(**sampling_params))

        output_filter = job_input.get('output_filter', [])
        return deep_filter(outputs, output_filter)
    except Exception as e:
        return {'error': str(e)}


runpod.serverless.start({"handler": handler})
