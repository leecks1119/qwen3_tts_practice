import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import soundfile as sf
import mlx.core as mx
import sounddevice as sd
from mlx_audio.tts.utils import load_model


# -----------------------------
# Text splitting (YouTube script friendly)
# -----------------------------
def normalize_text(text: str) -> str:
    # Normalize whitespace, keep newlines for paragraph meaning
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def split_into_segments(text: str, max_chars: int = 220) -> List[str]:
    """
    Split long script into manageable chunks.
    - Keep paragraphs
    - Prefer sentence boundaries
    - Fallback to hard cut
    """
    text = normalize_text(text)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    segments: List[str] = []

    # Sentence boundary heuristic for Korean/English punctuation
    sent_splitter = re.compile(r"(?<=[\.\!\?。！？…])\s+|(?<=\n)\s*")

    for para in paragraphs:
        # First, split into sentences
        sents = [s.strip() for s in sent_splitter.split(para) if s.strip()]
        buf = ""
        for s in sents:
            if not buf:
                buf = s
                continue
            # If adding keeps within limit, append
            if len(buf) + 1 + len(s) <= max_chars:
                buf = f"{buf} {s}"
            else:
                segments.append(buf)
                buf = s
        if buf:
            segments.append(buf)

    # Final pass: hard-cut any segment still too long
    final_segments: List[str] = []
    for seg in segments:
        if len(seg) <= max_chars:
            final_segments.append(seg)
        else:
            start = 0
            while start < len(seg):
                final_segments.append(seg[start : start + max_chars].strip())
                start += max_chars

    # Drop empty
    return [s for s in final_segments if s.strip()]


def silence(sr: int, seconds: float) -> np.ndarray:
    n = int(sr * seconds)
    return np.zeros(n, dtype=np.float32)


def to_float32_numpy(audio) -> np.ndarray:
    if isinstance(audio, np.ndarray):
        return audio.astype(np.float32, copy=False)

    # mlx.core.array requires mlx dtype in astype.
    if hasattr(audio, "astype"):
        try:
            return np.asarray(audio.astype(mx.float32), dtype=np.float32)
        except TypeError:
            pass

    return np.asarray(audio, dtype=np.float32)


def record_reference_audio(path: Path, sr: int, seconds: float) -> Path:
    n_samples = int(sr * seconds)
    print(f"[record] {seconds:.1f}s 녹음을 시작합니다. 준비되면 바로 말해주세요...")
    audio = sd.rec(n_samples, samplerate=sr, channels=1, dtype="float32")
    sd.wait()
    sf.write(str(path), audio.squeeze(-1), sr)
    print(f"[record] reference saved: {path}")
    return path


# -----------------------------
# TTS pipelines
# -----------------------------
@dataclass
class TTSConfig:
    outdir: Path
    language: str
    speaker: str
    custom_instruct: str
    max_chars: int
    sr: int = 24000

    # Models (MLX community)
    model_customvoice: str = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
    model_base: str = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16"
    model_voicedesign: str = "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16"


def generate_customvoice_segments(cfg: TTSConfig, segments: List[str]) -> List[Path]:
    model = load_model(cfg.model_customvoice)

    # Normalize speaker input and map aliases to known supported speakers.
    speaker_alias = {
        "haegeum": "sohee",
    }
    normalized_speaker = cfg.speaker.strip().lower()
    cfg.speaker = speaker_alias.get(normalized_speaker, normalized_speaker)

    if hasattr(model, "supported_speakers"):
        print("[info] supported_speakers:", model.supported_speakers)

    wav_paths: List[Path] = []

    for i, text in enumerate(segments, start=1):
        results = list(
            model.generate_custom_voice(
                text=text,
                speaker=cfg.speaker,
                language=cfg.language,
                instruct=cfg.custom_instruct,
            )
        )
        audio = to_float32_numpy(results[0].audio)
        out = cfg.outdir / f"{i:03d}.wav"
        sf.write(str(out), audio, cfg.sr)
        wav_paths.append(out)
        print(f"[{i}/{len(segments)}] saved: {out.name}")

    return wav_paths


def generate_voice_design_reference(cfg: TTSConfig, ref_text: str, voice_design_instruct: str) -> Path:
    design_model = load_model(cfg.model_voicedesign)
    results = list(
        design_model.generate_voice_design(
            text=ref_text,
            language=cfg.language,
            instruct=voice_design_instruct,
        )
    )
    ref_audio = to_float32_numpy(results[0].audio)
    out = cfg.outdir / "voice_ref.wav"
    sf.write(str(out), ref_audio, cfg.sr)
    print(f"[ref] voice reference saved: {out.name}")
    return out


def generate_clone_segments(cfg: TTSConfig, segments: List[str], ref_audio_path: str, ref_text: str) -> List[Path]:
    base_model = load_model(cfg.model_base)
    wav_paths: List[Path] = []

    for i, text in enumerate(segments, start=1):
        results = list(
            base_model.generate(
                text=text,
                ref_audio=ref_audio_path,
                ref_text=ref_text,
            )
        )
        audio = to_float32_numpy(results[0].audio)
        out = cfg.outdir / f"{i:03d}.wav"
        sf.write(str(out), audio, cfg.sr)
        wav_paths.append(out)
        print(f"[{i}/{len(segments)}] saved: {out.name}")

    return wav_paths


# -----------------------------
# Merge WAVs (optional)
# -----------------------------
def merge_with_ffmpeg(outdir: Path, wav_paths: List[Path], merged_name: str = "merged.wav") -> Path:
    """
    Merge wav files using ffmpeg concat demuxer.
    Requires: brew install ffmpeg
    """
    concat_file = outdir / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for p in wav_paths:
            # ffmpeg concat expects: file 'path'
            f.write(f"file '{p.resolve()}'\n")

    merged_path = outdir / merged_name
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(merged_path),
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[merge] merged saved: {merged_path.name}")
    except FileNotFoundError:
        print("[merge] ffmpeg not found. Install with: brew install ffmpeg")
    except subprocess.CalledProcessError:
        # Fallback: re-encode if stream copy fails (some wav headers differ)
        cmd2 = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            str(merged_path),
        ]
        subprocess.run(cmd2, check=False)
        print(f"[merge] merged (re-encoded) saved: {merged_path.name}")

    return merged_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Input script .txt")
    ap.add_argument("--outdir", required=True, help="Output directory")
    ap.add_argument(
        "--pipeline",
        choices=["customvoice", "voice_design_clone", "clone_with_ref"],
        default="voice_design_clone",
        help="TTS pipeline",
    )
    ap.add_argument("--language", default="Korean")
    ap.add_argument("--speaker", default="sohee", help="Used in customvoice pipeline")
    ap.add_argument("--custom_instruct", default="자연스럽고 또렷하게 읽어주세요")
    ap.add_argument("--max_chars", type=int, default=220, help="Max chars per segment")
    ap.add_argument("--merge", action="store_true", help="Merge segments into one wav via ffmpeg")

    # voice design -> clone
    ap.add_argument(
        "--voice_design_instruct",
        default="30대 남성, 차분하고 전문적인 목소리, 또렷한 발음",
        help="Used in voice_design_clone pipeline",
    )
    ap.add_argument(
        "--ref_text",
        default="안녕하세요 여러분, 오늘 영상에서는 중요한 내용을 간단하게 정리해드리겠습니다.",
        help="Reference text for voice design/clone",
    )

    # clone with provided ref
    ap.add_argument("--ref_audio", default="", help="Existing reference audio file path for clone_with_ref pipeline")
    ap.add_argument(
        "--record_ref",
        action="store_true",
        help="Record reference voice from microphone (used in clone_with_ref pipeline)",
    )
    ap.add_argument("--record_seconds", type=float, default=8.0, help="Reference recording duration in seconds")

    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with open(args.input, "r", encoding="utf-8") as f:
        raw = f.read()

    segments = split_into_segments(raw, max_chars=args.max_chars)
    if not segments:
        raise SystemExit("No segments found. Check input text.")

    # Save manifest
    manifest = {
        "input": str(Path(args.input).resolve()),
        "pipeline": args.pipeline,
        "language": args.language,
        "speaker": args.speaker,
        "custom_instruct": args.custom_instruct,
        "max_chars": args.max_chars,
        "segments": [{"index": i + 1, "text": t} for i, t in enumerate(segments)],
    }
    with open(outdir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    cfg = TTSConfig(
        outdir=outdir,
        language=args.language,
        speaker=args.speaker,
        custom_instruct=args.custom_instruct,
        max_chars=args.max_chars,
    )

    print(f"[info] segments: {len(segments)}")
    wav_paths: List[Path] = []

    if args.pipeline == "customvoice":
        wav_paths = generate_customvoice_segments(cfg, segments)

    elif args.pipeline == "voice_design_clone":
        # Step 1) Create reference voice audio (fixed narrator identity)
        ref_audio_path = generate_voice_design_reference(cfg, args.ref_text, args.voice_design_instruct)
        # Step 2) Clone that voice for all segments
        wav_paths = generate_clone_segments(cfg, segments, str(ref_audio_path), args.ref_text)

    elif args.pipeline == "clone_with_ref":
        ref_audio = args.ref_audio
        if args.record_ref:
            ref_audio_path = outdir / "my_voice_ref.wav"
            record_reference_audio(ref_audio_path, cfg.sr, args.record_seconds)
            ref_audio = str(ref_audio_path)

        if not ref_audio:
            raise SystemExit("--ref_audio is required for clone_with_ref pipeline (or use --record_ref)")
        if not Path(ref_audio).exists():
            raise SystemExit(f"ref_audio not found: {ref_audio}")
        wav_paths = generate_clone_segments(cfg, segments, ref_audio, args.ref_text)

    else:
        raise SystemExit("Unknown pipeline")

    # Optional: add small silences by physically inserting zeros (kept minimal for a test)
    # If you want silence between segments, merge with re-encode path instead of stream copy.
    # For now, we leave as is.

    if args.merge and wav_paths:
        merge_with_ffmpeg(outdir, wav_paths)

    print("[done]")

if __name__ == "__main__":
    main()
