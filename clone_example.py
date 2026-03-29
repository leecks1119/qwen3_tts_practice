import argparse

import soundfile as sf
from mlx_audio.tts.utils import load_model


def main() -> None:
    ap = argparse.ArgumentParser(description="Qwen3 TTS voice clone example for Apple Silicon Macs")
    ap.add_argument("--ref-audio", required=True, help="Reference audio path, e.g. ./ref.wav")
    ap.add_argument("--ref-text", required=True, help="Transcript of the reference audio")
    ap.add_argument(
        "--text",
        default="안녕하세요. 이 목소리로 새로운 문장을 읽는 보이스 클로닝 테스트입니다.",
        help="Target text to synthesize",
    )
    ap.add_argument("--output", default="output_clone.wav", help="Output wav path")
    ap.add_argument(
        "--model",
        default="mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16",
        help="MLX model id",
    )
    args = ap.parse_args()

    model = load_model(args.model)
    results = list(
        model.generate(
            text=args.text,
            ref_audio=args.ref_audio,
            ref_text=args.ref_text,
            lang_code="ko",
        )
    )

    sf.write(args.output, results[0].audio, 24000)
    print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
