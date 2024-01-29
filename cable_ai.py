from pgpt_python.client import PrivateGPTApi

client = PrivateGPTApi(base_url="http://localhost:8001")
print(client.health.health())


def query_without_context(msg, system_prompt):
    prompt_result = client.contextual_completions.prompt_completion(prompt=msg)
    return prompt_result.choices[0].message.content


def query_with_context(msg, system_prompt):


    result = client.contextual_completions.prompt_completion(
        system_prompt=system_prompt,
        prompt=msg,
    use_context=True,
    include_sources=True,).choices[0]
    answer = result.message.content + f" # Source: {result.sources[0].document.doc_metadata['file_name']}"

    return answer


