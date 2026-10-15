"""Offline verifier for the normalized WaveKat Qwen3 bundle catalog."""
from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "bundles.json"
SOURCE = ROOT / "catalog" / "source.json"
EXPECTED_TYPES = {"base-0.6b": "base", "voice-design-1.7b": "voice_design"}
QUALITIES = ("fp32", "int4")
GENERATION_COMPONENTS = {"talker_prefill", "talker_decode", "code_predictor", "vocoder"}
ENCODER_COMPONENTS = {"speaker_encoder", "tokenizer_encoder"}
TOKENIZER_FILES = {
    "tokenizer_json": "tokenizer.json",
    "vocab": "vocab.json",
    "merges": "merges.txt",
    "tokenizer_config": "tokenizer_config.json",
    "special_tokens": "special_tokens_map.json",
    "added_tokens": "added_tokens.json",
}
EMBEDDING_COMPONENTS = {
    "text_embedding",
    "text_projection_fc1_weight",
    "text_projection_fc1_bias",
    "text_projection_fc2_weight",
    "text_projection_fc2_bias",
    "talker_codec_embedding",
    *(f"cp_codec_embedding_{index}" for index in range(15)),
}
OPTIONAL_EMBEDDINGS = {"small_to_mtp_projection_bias", "small_to_mtp_projection_weight"}
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REPOSITORY_RE = re.compile(r"^[^/\\\s]+/[^/\\\s]+$")


def fail(message: str) -> None:
    raise SystemExit("catalog verification failed: " + message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def exact_keys(value: Any, expected: set[str], label: str) -> None:
    require(isinstance(value, dict), f"{label} must be an object")
    missing = expected - value.keys()
    extra = value.keys() - expected
    require(not missing and not extra,
            f"{label} fields mismatch (missing={sorted(missing)}, extra={sorted(extra)})")


def pinned_url(repository: str, revision: str, path: str) -> str:
    repo = "/".join(quote(part, safe="") for part in repository.split("/"))
    asset = quote(path, safe="/")
    return f"https://huggingface.co/{repo}/resolve/{revision}/{asset}?download=true"


def validate_artifact(
    bundle_id: str,
    artifact: Any,
    index: int,
    repository: str,
    revision: str,
    model_type: str,
    seen_paths: set[str],
    seen_keys: set[tuple[str, str | None, str | None]],
    model_components: dict[str | None, set[str]],
    data_components: dict[str | None, set[str]],
    tokenizer_components: set[str],
    embedding_components: set[str],
) -> None:
    label = f"{bundle_id}: artifact {index}"
    exact_keys(artifact, {"role", "component", "quality", "path", "url", "size", "sha256"}, label)
    role = artifact["role"]
    component = artifact["component"]
    quality = artifact["quality"]
    path = artifact["path"]
    require(isinstance(role, str) and role in {"config", "tokenizer", "embedding", "model", "model_data"},
            f"{label}: unsupported artifact role {role!r}")
    require(component is None or isinstance(component, str) and ID_RE.fullmatch(component),
            f"{label}: invalid component {component!r}")
    require(quality is None or quality in QUALITIES, f"{label}: invalid quality {quality!r}")
    require(isinstance(path, str) and path and not path.startswith("/") and "\\" not in path,
            f"{label}: unsafe artifact path {path!r}")
    require(all(part not in {"", ".", ".."} for part in path.split("/")),
            f"{label}: unsafe artifact path {path!r}")
    require(str(PurePosixPath(path)) == path, f"{label}: non-canonical artifact path {path!r}")
    require(path not in seen_paths, f"{bundle_id}: duplicate artifact path {path!r}")
    seen_paths.add(path)
    key = (role, component, quality)
    require(key not in seen_keys, f"{bundle_id}: duplicate role/component/quality {key!r}")
    seen_keys.add(key)

    if role == "config":
        require(component is None and quality is None and path == "config.json",
                f"{label}: config must be the shared config.json artifact")
    elif role == "tokenizer":
        require(component in TOKENIZER_FILES and quality is None,
                f"{label}: invalid tokenizer component or quality")
        require(path == f"tokenizer/{TOKENIZER_FILES[component]}",
                f"{label}: tokenizer path disagrees with component {component!r}")
        tokenizer_components.add(component)
    elif role == "embedding":
        require(component in EMBEDDING_COMPONENTS | OPTIONAL_EMBEDDINGS and quality is None,
                f"{label}: invalid embedding component or quality")
        require(path == f"embeddings/{component}.npy",
                f"{label}: embedding path disagrees with component {component!r}")
        embedding_components.add(component)
    else:
        is_generation = component in GENERATION_COMPONENTS
        is_encoder = model_type == "base" and component in ENCODER_COMPONENTS
        require(is_generation or is_encoder, f"{label}: unknown model component {component!r}")
        if is_generation:
            require(quality in QUALITIES, f"{label}: generation graph must select fp32 or int4")
            graph_path = f"{quality}/{component}.onnx"
        else:
            require(quality is None, f"{label}: Base encoders must be shared across profiles")
            graph_path = f"{component}.onnx"
        expected_path = graph_path + ".data" if role == "model_data" else graph_path
        require(path == expected_path, f"{label}: path disagrees with {role}:{component}:{quality}")
        destination = model_components if role == "model" else data_components
        destination.setdefault(quality, set()).add(component)

    require(artifact["url"] == pinned_url(repository, revision, path),
            f"{label}: URL is not pinned to its source and path")
    require(type(artifact["size"]) is int and artifact["size"] > 0,
            f"{label}: size must be a positive integer")
    require(isinstance(artifact["sha256"], str) and SHA256_RE.fullmatch(artifact["sha256"]),
            f"{label}: sha256 must be lowercase 64-character hex")


def validate_bundle(bundle_id: str, bundle: Any, aliases_seen: set[str]) -> dict[str, str]:
    label = f"{bundle_id}: bundle"
    exact_keys(bundle, {
        "id", "aliases", "layout", "model_type", "sample_rate", "source", "profiles", "artifacts"
    }, label)
    require(bundle["id"] == bundle_id, f"{bundle_id}: bundle map key does not match id")
    model_type = EXPECTED_TYPES[bundle_id]
    require(bundle["model_type"] == model_type, f"{bundle_id}: model_type must be {model_type!r}")
    require(bundle["layout"] == "qwen3-wavekat-v1", f"{bundle_id}: unsupported layout")
    require(type(bundle["sample_rate"]) is int and bundle["sample_rate"] == 24000,
            f"{bundle_id}: sample_rate must be 24000")

    aliases = bundle["aliases"]
    require(isinstance(aliases, list) and aliases, f"{bundle_id}: aliases must be a non-empty list")
    for alias in aliases:
        require(isinstance(alias, str) and ID_RE.fullmatch(alias), f"{bundle_id}: unsafe alias {alias!r}")
        require(alias not in aliases_seen, f"duplicate or ambiguous alias/id {alias!r}")
        aliases_seen.add(alias)

    source = bundle["source"]
    exact_keys(source, {"provider", "repository", "revision", "license"}, f"{bundle_id}: source")
    require(source["provider"] == "huggingface", f"{bundle_id}: provider must be huggingface")
    repository = source["repository"]
    require(isinstance(repository, str) and REPOSITORY_RE.fullmatch(repository),
            f"{bundle_id}: invalid repository")
    revision = source["revision"]
    require(isinstance(revision, str) and REVISION_RE.fullmatch(revision),
            f"{bundle_id}: revision must be an immutable lowercase 40-character SHA")
    require(isinstance(source["license"], str) and source["license"],
            f"{bundle_id}: license is required")

    profiles = bundle["profiles"]
    exact_keys(profiles, set(QUALITIES), f"{bundle_id}: profiles")
    required_models = set(GENERATION_COMPONENTS)
    if model_type == "base":
        required_models.update(ENCODER_COMPONENTS)
    for quality in QUALITIES:
        profile = profiles[quality]
        exact_keys(profile, {"components"}, f"{bundle_id}/{quality}: profile")
        components = profile["components"]
        require(isinstance(components, list) and components == sorted(required_models),
                f"{bundle_id}/{quality}: profile has missing, extra, or non-canonical model components")

    artifacts = bundle["artifacts"]
    require(isinstance(artifacts, list) and artifacts, f"{bundle_id}: artifacts must be a non-empty list")
    seen_paths: set[str] = set()
    seen_keys: set[tuple[str, str | None, str | None]] = set()
    model_components: dict[str | None, set[str]] = {}
    data_components: dict[str | None, set[str]] = {}
    tokenizer_components: set[str] = set()
    embedding_components: set[str] = set()
    for index, artifact in enumerate(artifacts):
        validate_artifact(
            bundle_id, artifact, index, repository, revision, model_type, seen_paths, seen_keys,
            model_components, data_components, tokenizer_components, embedding_components
        )
    artifact_order = [
        (artifact["role"], artifact["component"] or "", artifact["quality"] or "", artifact["path"])
        for artifact in artifacts
    ]
    require(artifact_order == sorted(artifact_order),
            f"{bundle_id}: artifacts are not in canonical role/component/quality/path order")

    require(sum(artifact["role"] == "config" for artifact in artifacts) == 1,
            f"{bundle_id}: exactly one config artifact is required")
    require(tokenizer_components == set(TOKENIZER_FILES),
            f"{bundle_id}: incomplete tokenizer artifact inventory")
    require(EMBEDDING_COMPONENTS <= embedding_components <= EMBEDDING_COMPONENTS | OPTIONAL_EMBEDDINGS,
            f"{bundle_id}: incomplete or unsupported embedding artifact inventory")
    shared_models = set(ENCODER_COMPONENTS) if model_type == "base" else set()
    require(model_components.get(None, set()) == shared_models,
            f"{bundle_id}: missing or unexpected shared model components")
    require(data_components.get(None, set()) == shared_models,
            f"{bundle_id}: missing shared model external-data dependencies")
    for quality in QUALITIES:
        require(model_components.get(quality, set()) == GENERATION_COMPONENTS,
                f"{bundle_id}/{quality}: missing required model components")
        require(data_components.get(quality, set()) == GENERATION_COMPONENTS,
                f"{bundle_id}/{quality}: missing external-data dependencies")

    return {
        "id": bundle_id,
        "license": source["license"],
        "repository": repository,
        "revision": revision,
    }


def main() -> int:
    try:
        catalog_text = CATALOG.read_text(encoding="utf-8")
        source_text = SOURCE.read_text(encoding="utf-8")
        catalog = json.loads(catalog_text)
        source_snapshot = json.loads(source_text)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"unable to read valid catalog/source JSON: {exc}")

    exact_keys(catalog, {"schema", "kind", "source", "bundles"}, "catalog")
    require(type(catalog["schema"]) is int and catalog["schema"] == 1, "wrong catalog schema")
    require(catalog["kind"] == "qwen3-onnx-bundle-catalog", "wrong catalog kind")
    catalog_source = catalog["source"]
    exact_keys(catalog_source, {"provider", "bundle_count"}, "catalog source")
    require(catalog_source == {"provider": "huggingface", "bundle_count": 2},
            "catalog source metadata is invalid")
    bundles = catalog["bundles"]
    require(isinstance(bundles, dict) and set(bundles) == set(EXPECTED_TYPES),
            "catalog must contain exactly the supported Base and VoiceDesign bundles")

    aliases_seen = set(bundles)
    source_entries = [validate_bundle(bundle_id, bundles[bundle_id], aliases_seen)
                     for bundle_id in sorted(bundles)]
    exact_keys(source_snapshot, {"kind", "schema", "sources"}, "source snapshot")
    require(type(source_snapshot["schema"]) is int and source_snapshot["schema"] == 1,
            "source snapshot schema must be 1")
    require(source_snapshot["kind"] == "qwen3-onnx-source-snapshot",
            "wrong source snapshot kind")
    require(source_snapshot["sources"] == source_entries,
            "source snapshot does not match catalog provenance")

    require(catalog_text == json.dumps(catalog, indent=2, sort_keys=True) + "\n",
            "catalog JSON is not canonical sorted serialization")
    require(source_text == json.dumps(source_snapshot, indent=2, sort_keys=True) + "\n",
            "source JSON is not canonical sorted serialization")
    print(f"ok: {len(bundles)} normalized bundles, {len(aliases_seen)} unique ids/aliases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
