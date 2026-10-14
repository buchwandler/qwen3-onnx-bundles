#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "bundles.json"


def fail(message: str) -> None:
    raise SystemExit("catalog verification failed: " + message)


def main() -> int:
    obj = json.loads(CATALOG.read_text(encoding="utf-8"))
    if obj.get("schema") != 1 or obj.get("kind") != "qwen3-onnx-bundle-catalog": fail("wrong schema/kind")
    bundles = obj.get("bundles")
    if not isinstance(bundles, dict) or not bundles: fail("bundles must be a non-empty object")
    aliases: dict[str,str] = {}
    for bid, b in bundles.items():
        if b.get("layout") != "qwen3-wavekat-v1": fail(f"{bid}: unsupported layout")
        if b.get("model_type") not in {"voice_design","base","custom_voice"}: fail(f"{bid}: invalid model_type")
        src = b.get("source", {})
        if src.get("provider") != "huggingface": fail(f"{bid}: provider must be huggingface")
        if not re.fullmatch(r"[0-9a-f]{40}", str(src.get("revision",""))): fail(f"{bid}: revision must be 40 hex chars")
        if "/" not in str(src.get("repository","")): fail(f"{bid}: invalid repository")
        for alias in [bid, *b.get("aliases", [])]:
            prev = aliases.setdefault(alias, bid)
            if prev != bid: fail(f"duplicate alias {alias}: {prev}, {bid}")
        profiles = b.get("profiles", {})
        if not profiles: fail(f"{bid}: no profiles")
        for quality, p in profiles.items():
            inc = p.get("include", [])
            if not inc: fail(f"{bid}:{quality}: empty include")
            if any(x.startswith("/") or ".." in Path(x).parts or "\\" in x for x in inc): fail(f"{bid}:{quality}: unsafe include path")
            required = {"config.json", "tokenizer/*", "embeddings/*"}
            if not required.issubset(set(inc)): fail(f"{bid}:{quality}: missing common assets")
            for role in ("talker_prefill", "talker_decode", "code_predictor", "vocoder"):
                if not any(role in x for x in inc): fail(f"{bid}:{quality}: missing role {role}")
        if b["model_type"] == "base":
            flat = {x for p in profiles.values() for x in p["include"]}
            for name in ("speaker_encoder.onnx", "tokenizer_encoder.onnx"):
                if name not in flat: fail(f"{bid}: missing {name}")
    canonical = json.dumps(obj, indent=2, sort_keys=True) + "\n"
    if CATALOG.read_text(encoding="utf-8") != canonical: fail("catalog JSON is not canonical sorted serialization")
    print(f"ok: {len(bundles)} bundles, {len(aliases)} ids/aliases")
    return 0

if __name__ == "__main__": raise SystemExit(main())
