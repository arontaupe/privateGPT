from pgpt_python.client import PrivateGPTApi

client = PrivateGPTApi(base_url="http://localhost:8001")
print(client.health.health())


prompt_result = client.contextual_completions.prompt_completion(
    prompt="Answer with just the result: 2+2"
)
print(prompt_result.choices[0].message.content)


result = client.contextual_completions.prompt_completion(
    prompt="What is radio Liberty?",
    use_context=True,
    include_sources=True,
).choices[0]

print("\n>Contextual completion:")
print(result.message.content)
print(f" # Source: {result.sources[0].document.doc_metadata['file_name']}")