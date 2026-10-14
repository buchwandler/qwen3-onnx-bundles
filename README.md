# qwen3-onnx-bundles

Catalog-only companion repository for `qwen3synth`. It contains normalized Qwen3-TTS ONNX bundle metadata and no model weights, Python package, downloader, inference runtime, or `src/` tree.

## MVP entries

- `voice-design-1.7b` → `wavekat/Qwen3-TTS-1.7B-VoiceDesign-ONNX`, pinned to `62c7863a68800d72bcee4f2931148c441571ace7`.
- `base-0.6b` → `wavekat/Qwen3-TTS-0.6B-Base-ONNX`, pinned to `177cd39e2ddab0d4d7ce5152a7abc2d382621158`.
- Profiles: `int4`, `fp32`.
- Layout ABI: `qwen3-wavekat-v1`.

The MVP catalog intentionally uses **pinned upstream revisions plus include patterns** rather than pretending that unverified checksums have already been materialized. `qwen3synth` hashes every downloaded byte into its installation manifest. A production catalog release should replace pattern-only integrity with a fully materialized per-file hash/size snapshot.

## Validate

```bash
python scripts/verify_catalog.py
```

## Versioning

This repository is data, not a PyPI distribution. There is therefore no hard-coded Python package version. Catalog compatibility is the integer `schema` field; repository release versions are Git tags. Consumers should pin a Git commit or release tag. This keeps versioning dynamic at the repository level and avoids a duplicated version constant.

## Use with qwen3synth

When hosted, pass the raw catalog URL:

```bash
qwen3synth models install base-0.6b --quality int4 --catalog https://.../catalog/bundles.json
```
