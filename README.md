# Qwen3 TTS for Mac (MLX)

Apple Silicon 맥북에서 `Qwen3-TTS`를 `MLX` 기반으로 바로 실행할 수 있게 정리한 리포지토리입니다.

이 리포는 아래 두 가지를 바로 해볼 수 있게 구성되어 있습니다.

- 기본 한국어 TTS
- 레퍼런스 음성을 이용한 Voice Clone

## 요구사항

- macOS
- Apple Silicon Mac (`M1`, `M2`, `M3`, `M4`)
- Xcode Command Line Tools
- `ffmpeg`
- Python `3.12+`

참고:

- 첫 실행 시 Hugging Face에서 모델을 자동 다운로드합니다.
- 모델 용량이 커서 디스크 여유 공간은 `20GB 이상` 권장합니다.

## 1. 클론

```bash
git clone <YOUR_GITHUB_REPO_URL>
cd qwen3_tts
```

## 2. 설치

가장 쉬운 방법:

```bash
make setup
```

위 명령은 아래 작업을 자동으로 진행합니다.

- `ffmpeg` 확인 또는 설치
- `.venv` 생성
- `pip` 업그레이드
- `requirements.txt` 설치

직접 하고 싶다면:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. 기본 테스트

```bash
source .venv/bin/activate
python test.py
```

정상 동작 시 `output_custom.wav` 가 생성됩니다.

## 4. 기본 한국어 TTS 예제

```bash
source .venv/bin/activate
python tts_youtube_batch.py \
  --input script.txt \
  --outdir out_wavs_demo \
  --pipeline customvoice \
  --speaker sohee \
  --language Korean \
  --custom_instruct "따뜻하고 친근하게 읽어주세요" \
  --merge
```

결과물:

- `out_wavs_demo/001.wav`
- `out_wavs_demo/merged.wav`

## 5. Voice Clone 가장 간단한 실행

먼저 `ref.wav` 를 준비합니다.

- 3초 이상 권장
- 주변 소음이 적을수록 좋음
- `ref_text` 는 실제 발화 내용과 최대한 정확히 맞추는 것이 좋음

실행:

```bash
source .venv/bin/activate
python clone_example.py \
  --ref-audio ./ref.wav \
  --ref-text "안녕하세요. 제 목소리 샘플입니다." \
  --text "이제 이 목소리로 새로운 문장을 읽습니다." \
  --output output_clone.wav
```

## 6. 긴 원고를 Voice Clone으로 생성

```bash
source .venv/bin/activate
python tts_youtube_batch.py \
  --input script2.txt \
  --outdir out_wavs_clone \
  --pipeline clone_with_ref \
  --ref_audio ./ref.wav \
  --ref_text "안녕하세요. 제 목소리 샘플입니다." \
  --merge
```

## 7. 지원 스피커

현재 설치본에서 확인된 `CustomVoice` 스피커:

- `serena`
- `vivian`
- `uncle_fu`
- `ryan`
- `aiden`
- `ono_anna`
- `sohee`
- `eric`
- `dylan`

한국어 시작용으로는 `sohee` 가 가장 안전합니다.

## 8. 자주 막히는 문제

### `Speaker 'Haegeum' not supported`

현재 설치본에서는 지원되지 않는 스피커입니다. `sohee` 로 바꿔서 실행하세요.

### `ffmpeg not found`

```bash
brew install ffmpeg
```

### 처음 실행이 오래 걸림

정상일 가능성이 큽니다. 첫 실행 시 모델 다운로드가 자동으로 진행됩니다.

### tokenizer 관련 경고가 보임

일부 경고 문구가 보일 수 있지만, `wav` 파일이 정상 생성되면 우선 계속 진행해도 됩니다.

## 9. 배포 시 포함하지 말 것

아래는 GitHub에 올리지 않는 것을 권장합니다.

- `.venv/`
- `qwen-tts-env/`
- `out_wavs/`
- `out_wavs_*`
- 생성된 오디오 파일

`.gitignore` 에 이미 반영되어 있습니다.

## 10. 참고 링크

- [Qwen3-TTS GitHub](https://github.com/QwenLM/Qwen3-TTS)
- [Qwen3-TTS PyPI](https://pypi.org/project/qwen-tts/)
- [MLX-Audio GitHub](https://github.com/Blaizzy/mlx-audio)
- [MLX Base Model](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16)
- [MLX CustomVoice Model](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16)
