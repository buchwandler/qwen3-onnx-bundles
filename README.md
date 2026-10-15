# qwen3-onnx-bundles

Catalog-only companion repository for the OnnxVoice Qwen3 runtime and Qwen3Synth frontend. It contains normalized Qwen3-TTS ONNX bundle metadata and no model weights, Python package, downloader, inference runtime, or `src/` tree.

## MVP entries

- `voice-design-1.7b` → `wavekat/Qwen3-TTS-1.7B-VoiceDesign-ONNX`, pinned to `62c7863a68800d72bcee4f2931148c441571ace7`.
- `base-0.6b` → `wavekat/Qwen3-TTS-0.6B-Base-ONNX`, pinned to `177cd39e2ddab0d4d7ce5152a7abc2d382621158`.
- Profiles: `int4`, `fp32`.
- Layout ABI: `qwen3-wavekat-v1`.

The normalized catalog lists each selected artifact with its role, component, quality, source path, immutable-revision URL, byte size, and SHA-256, including ONNX external-data files. `python scripts/verify_catalog.py` checks the complete inventory and provenance offline; OnnxVoice owns download-time integrity verification.

## Validate

```bash
python scripts/verify_catalog.py
```

## Versioning

This repository is data, not a PyPI distribution. There is therefore no hard-coded Python package version. Catalog compatibility is the integer `schema` field; repository release versions are Git tags. Consumers should pin a Git commit or release tag. This keeps versioning dynamic at the repository level and avoids a duplicated version constant.

## Use with OnnxVoice and Qwen3Synth

OnnxVoice consumes this normalized catalog and owns bundle acquisition, integrity checks, managed installation, providers, graph validation, and inference. Qwen3Synth uses OnnxVoice for the model runtime while retaining its tokenizer, chat templates, WAV handling, profiles, and user-facing synthesis API. See the [OnnxVoice Qwen3 contract](https://github.com/buchwandler/onnxvoice/blob/main/docs/systems/qwen3.md).

```bash
onnxvoice install qwen3:base-0.6b --quality int4
qwen3synth models install base-0.6b --quality int4 --catalog https://.../catalog/bundles.json
```
