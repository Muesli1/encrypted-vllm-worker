import runpod
from vllm import LLM, SamplingParams

prompts = [
    "Hello, my name is",
    "The president of the United States is",
    "The capital of France is",
    "The future of AI is",
]
sampling_params = SamplingParams(temperature=0.8, top_p=0.95)
llm = LLM(model="facebook/opt-125m")


def handler(job):
    job_input = job['input']

    prompt = job_input.get('prompt', False)
    if not prompt:
        return {'error': 'Missing "prompt" key in input!'}

    output = llm.generate(prompt, sampling_params)[0]

    return output.outputs[0].text


runpod.serverless.start({"handler": handler})
