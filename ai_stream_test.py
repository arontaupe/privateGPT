# this script is used to test the AI with streaming responses.
# does not work yet, likely due to python 3.12 not being supported by Llama Index yet
from pgpt_python.client import PrivateGPTApi
import asyncio
from openai_streaming import process_response
from typing import AsyncGenerator


debug = True

try:
    print('---connecting to the AI---')
    client = PrivateGPTApi(base_url="http://localhost:8001", timeout=60)
    print(client.health.health())
except Exception as e:
    print("Could not connect to Cable AI. Is it running? Please run './start_ai.sh' in a separate terminal.")
    exit()

async def query_with_context(msg, system_prompt):
    response = None  # Initialize the response variable

    if client.health.health():
        try:
            response = client.contextual_completions.prompt_completion(
                system_prompt=system_prompt,
                prompt=msg,
                use_context=True,
                include_sources=True,
                stream=True
            )
            await process_response(resp, content_handler)
        except Exception as e:
            print(f"An error occurred: {e}")

    else:
        print("AI offline")

    if response and response.content:
        try:
            for chunk in response:
                if chunk.content:
                    print(chunk.content)
                    # Handle the content as needed
        except Exception as e:
            print(f"An error occurred while processing the response: {e}")
    else:
        print("No response from AI")

    return response

print("Testing AI with context")
asyncio.run(query_with_context("What is the meaning of life?", "The meaning of life is"))

