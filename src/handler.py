import os
import json

import runpod
from vllm import LLM, SamplingParams



model_name = os.getenv("VLLM_MODEL_NAME")
llm_parameters = os.getenv("VLLM_ENGINE_PARAMETERS")
if llm_parameters is None:
    llm_paramters = "{}"

llm = LLM(model=model_name, **json.loads(llm_parameters))

def handler(job):
    job_input = job['input']

    prompt = job_input.get('prompt', False)
    sampling_params = job_input.get('parameters', {})

    if not prompt:
        return {'error': 'Missing "prompt" key in input!'}

    return llm.generate(prompt, SamplingParams(**sampling_params))


runpod.serverless.start({"handler": handler})
