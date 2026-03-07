# Khaya SDK

[![PyPI version](https://badge.fury.io/py/khaya.svg)](https://pypi.org/project/khaya/)
[![CI](https://github.com/Khaya-AI/khaya-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/Khaya-AI/khaya-sdk/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Khaya-AI/khaya-sdk/blob/main/LICENSE)

Python SDK for the [GhanaNLP](https://ghananlp.org) Khaya API — providing **translation**, **automatic speech recognition (ASR)**, and **text-to-speech (TTS)** for African languages.

## Install

```bash
pip install khaya
```

## Quick start

```python
import os
from khaya import KhayaClient

with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
    result = khaya.translate("Hello, how are you?", "en-tw")
    print(result.json())  # "Ɛte sɛn?"
```

Ready to go further? Head to the [Getting Started](getting-started.md) guide.
