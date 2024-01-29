# How to run the cable_ai

## Setup

PLS Skip if already setup. you will break stuff!!

[Follow instructions](https://docs.privategpt.dev/installation)

```bash
git clone <https://github.com/imartinez/privateGPT>
cd privateGPT


pyenv install 3.11
pyenv install 3.12
pyenv local 3.12

poetry install --with local

poetry run python scripts/setup

# this is rather iomportant, otherwise gpu not recognized and will run on cpu
CMAKE_ARGS="-DLLAMA_METAL=on" pip install --force-reinstall --no-cache-dir llama-cpp-python


make run
```

-- server should now run on localhost:8001
(open in browser to check)

## Run the cable_ai

Optional: install the SDK:

```bash
pip install pgpt_python
```

execute cable_ai

```bash
python cable_ai.py
```

## Optimizations made

in settings.yaml, change the following:

```yaml

llm:
  mode: local
  # Should be matching the selected model
  max_new_tokens: 128
  context_window: 2000
  tokenizer: mistralai/Mistral-7B-Instruct-v0.2
```
