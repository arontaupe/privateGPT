# How to run the cable_AI

this is a documentation file detailing the steps necessary to operate and install the cable AI.

## update notice

All scripts are aliased now. Open a terminal and type:

this will start the AI server (and the UI under <http://localhost:8001>

```bash
aether
```

once started, open a !!separate!! terminal (while the old one stays active) and type:
this script assumes that aether has been executed before and is running.
it also assumes that a LoRa device is connected via serial (through USB)

```bash
mesh
```

now the setup should be up and running. open the Meshtastic app on your phone and connect to the device to start chatting

<https://meshtastic.org/downloads>

## Setup

PLS Skip if already setup. You will break stuff!!

[Follow instructions](https://docs.privategpt.dev/installation)

```bash
git clone https://github.com/imartinez/privateGPT
cd privateGPT
```

```bash
cd
pyenv install 3.11
pyenv install 3.12
pyenv local 3.12
```

```bash
poetry install --with local
poetry install --with ui
```

```bash
poetry run python scripts/setup
```

## this is rather important, otherwise gpu is not recognized and will run on cpu

```bash
# only valid for silicon macs
CMAKE_ARGS="-DLLAMA_METAL=on" pip install --force-reinstall --no-cache-dir llama-cpp-python
```

```bash
make run
# or cleaner:
PGPT_PROFILES=local make run
```

-- server should now run on
<http://localhost:8001>
(open in browser to check)

## Switching between python versions

```bash
pyenv which python  # should show the current version
pyenv local 3.12  # switch to 3.12
pyenv local 3.11  # switch to 3.11
```

## Run the cable_ai

Optional: install the SDK:

```bash
pip install pgpt_python
```

execute cable_ai

```bash
python cable_ai.py
```

edit: now the main execution moved over to meshtastic_handler.py

new execution command:

```bash
python aethercomms_old.py
```

## Ingest Documents

read in all documents from the training docs folder

```bash
make ingest /Users/aron/sdr/ai_narration/ai_training_docs -- --watch --log-file //Users/aron/privateGPT/private_gpt/ingest.log
```

## Delete all documents

deletes all ingested documents, useful when trying to get rid of a trained doc.

```bash
make wipe
```

## Optimizations made

Should not be necessary to change for operation, changes are persistent

in settings.yaml, change the following:

```yaml
llm:
  mode: local
  # Should be matching the selected model
  max_new_tokens: 128
  context_window: 2000
  tokenizer: mistralai/Mistral-7B-Instruct-v0.2
```
