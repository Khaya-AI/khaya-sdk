# Khaya SDK

[![PyPI](https://img.shields.io/pypi/v/khaya)](https://pypi.org/project/khaya/)
[![Python versions](https://img.shields.io/pypi/pyversions/khaya)](https://pypi.org/project/khaya/)
[![CI](https://github.com/Khaya-AI/khaya-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/Khaya-AI/khaya-sdk/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/khaya)](https://github.com/Khaya-AI/khaya-sdk/blob/main/LICENSE)

Python SDK for the [Khaya AI](https://khaya.ai) API, built on [GhanaNLP](https://ghananlp.org) —
**translation**, **automatic speech recognition (ASR)**, and **text-to-speech (TTS)**
across 30+ African languages.

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
    print(result.text)  # the Twi translation
```

Ready to go further? Head to the [Getting Started](getting-started.md) guide, or
browse the [language reference](languages.md).
