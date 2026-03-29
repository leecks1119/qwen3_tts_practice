# Qwen3 TTS 맥북 세팅 가이드

이 문서는 현재 이 폴더에서 실제로 동작 확인한 Qwen3 TTS 세팅을 기준으로, 수강생들이 맥북에서 처음부터 그대로 따라 할 수 있게 정리한 안내서입니다.

## 0. 수업 전에 먼저 확인할 것

- 이 세팅은 Apple Silicon 맥북(M1, M2, M3, M4 계열) 기준입니다.
- 현재 확인된 파이썬 버전은 `Python 3.14.3` 입니다.
- 현재 확인된 핵심 패키지 버전은 아래와 같습니다.
  - `mlx-audio==0.3.1`
  - `mlx==0.30.6`
  - `transformers==5.0.0rc3`
- 모델 캐시가 커서 디스크 여유 공간을 넉넉하게 잡는 것이 좋습니다.
  - `CustomVoice` 약 `4.2GB`
  - `Base` 약 `4.2GB`
  - `VoiceDesign` 도 추가 다운로드가 발생할 수 있으므로 전체적으로 `20GB 이상` 여유 권장

## 1. 수강생에게 배포할 폴더

수강생에게는 이 프로젝트 폴더를 압축해서 전달하되, 아래 폴더는 빼고 주는 것을 권장합니다.

- `qwen-tts-env/`
- `out_wavs/`
- `out_wavs_*`
- `__pycache__/`

즉, 코드와 예제 텍스트 파일만 전달하고, 가상환경과 모델 다운로드는 각자 맥북에서 새로 진행합니다.

## 2. 기본 프로그램 설치

터미널을 열고 아래 순서대로 진행합니다.

### 2-1. Xcode Command Line Tools 설치

```bash
xcode-select --install
```

이미 설치되어 있으면 안내창만 뜨고 끝납니다.

### 2-2. Homebrew 설치

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

설치 후 확인:

```bash
brew -v
```

### 2-3. 필수 도구 설치

```bash
brew install pyenv ffmpeg git
```

- `pyenv`: 현재 PC와 같은 파이썬 버전으로 맞추기 위해 사용
- `ffmpeg`: 여러 개의 WAV를 하나로 합칠 때 사용
- `git`: 필요시 프로젝트 다운로드용

## 3. pyenv 설정

`zsh` 기준으로 아래를 실행합니다.

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zprofile
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zprofile
echo 'eval "$(pyenv init - zsh)"' >> ~/.zprofile
exec zsh
```

정상 확인:

```bash
pyenv --version
```

## 4. Python 3.14.3 설치

현재 세팅과 동일하게 맞추려면 아래처럼 진행합니다.

```bash
pyenv install 3.14.3
pyenv global 3.14.3
python3 -V
```

정상이라면 아래처럼 보여야 합니다.

```bash
Python 3.14.3
```

## 5. 프로젝트 폴더 받기

예시:

1. 압축파일로 받았다면 압축을 풉니다.
2. 터미널에서 해당 폴더로 이동합니다.

```bash
cd ~/Desktop/qwen3_tts
```

## 6. 가상환경 만들기

프로젝트 폴더 안에서 실행:

```bash
python3 -m venv qwen-tts-env
source qwen-tts-env/bin/activate
python -V
```

프롬프트 앞에 `(qwen-tts-env)` 가 붙으면 정상입니다.

## 7. 패키지 설치

이 폴더에는 현재 PC에서 추출한 고정 버전 파일 `requirements-macos-lock.txt` 가 있습니다. 가장 안전한 방법은 이 파일로 그대로 설치하는 것입니다.

```bash
pip install --upgrade pip
pip install -r requirements-macos-lock.txt
```

설치 확인:

```bash
pip show mlx-audio mlx transformers sounddevice soundfile
```

선택 사항:

- Hugging Face 다운로드 속도를 높이고 싶다면 계정을 만든 뒤 토큰 로그인을 사용할 수 있습니다.
- 토큰 없이도 실행은 가능하지만, 처음 다운로드가 느릴 수 있습니다.

## 8. 첫 실행 테스트

가장 간단한 테스트는 `test.py` 입니다.

```bash
python test.py
```

정상 실행되면 현재 폴더에 `output_custom.wav` 파일이 생성됩니다.

주의:

- 현재 설치본에서 확인된 지원 스피커는 아래와 같습니다.
  - `serena`
  - `vivian`
  - `uncle_fu`
  - `ryan`
  - `aiden`
  - `ono_anna`
  - `sohee`
  - `eric`
  - `dylan`
- 예전 예시처럼 `Haegeum` 을 넣으면 에러가 납니다.
- 한국어는 `sohee` 로 시작하는 것이 가장 안전합니다.

## 9. 배치 TTS 실행 방법

이 프로젝트의 실제 수업용 메인 스크립트는 `tts_youtube_batch.py` 입니다.

### 9-1. 기본 커스텀 보이스 생성

```bash
python tts_youtube_batch.py \
  --input script.txt \
  --outdir out_wavs_basic \
  --pipeline customvoice \
  --speaker sohee \
  --language Korean \
  --custom_instruct "자연스럽고 친근하게 읽어주세요" \
  --merge
```

결과:

- `out_wavs_basic/001.wav`
- `out_wavs_basic/manifest.json`
- `out_wavs_basic/merged.wav`

### 9-2. Voice Design 후 클로닝

```bash
python tts_youtube_batch.py \
  --input script.txt \
  --outdir out_wavs_design \
  --pipeline voice_design_clone \
  --language Korean \
  --voice_design_instruct "30대 남성, 차분하고 전문적인 목소리, 또렷한 발음" \
  --ref_text "안녕하세요 여러분, 오늘 영상에서는 중요한 내용을 간단하게 정리해드리겠습니다." \
  --merge
```

### 9-3. 내 목소리 레퍼런스로 클로닝

이미 준비된 레퍼런스 음성이 있다면:

```bash
python tts_youtube_batch.py \
  --input script2.txt \
  --outdir out_wavs_myvoice \
  --pipeline clone_with_ref \
  --ref_audio ./sample_ref.wav \
  --ref_text "안녕하세요. 제 목소리 레퍼런스입니다." \
  --merge
```

직접 마이크로 녹음하려면:

```bash
python tts_youtube_batch.py \
  --input script2.txt \
  --outdir out_wavs_myvoice \
  --pipeline clone_with_ref \
  --record_ref \
  --record_seconds 8 \
  --ref_text "안녕하세요. 제 목소리 레퍼런스입니다." \
  --merge
```

이 경우 macOS에서 마이크 권한 허용창이 뜰 수 있습니다.

## 10. 수업 중 꼭 설명할 포인트

### 첫 실행 시 모델 다운로드

- 첫 실행은 시간이 조금 걸립니다.
- Hugging Face에서 모델 파일을 자동 다운로드합니다.
- 인터넷이 느리면 오래 걸릴 수 있습니다.
- 같은 맥북에서는 두 번째 실행부터 훨씬 빨라집니다.

### `--merge` 옵션

- `--merge` 를 쓰면 `ffmpeg` 로 여러 WAV를 하나로 합칩니다.
- `ffmpeg` 가 없으면 merge 단계에서 안내 메시지가 나옵니다.

### 텍스트 분할

- 긴 문장은 자동으로 여러 개의 오디오로 나눠집니다.
- 기본 분할 길이는 `--max_chars 220` 입니다.

## 11. 자주 막히는 문제

### 1) `Speaker 'Haegeum' not supported`

원인:

- 현재 설치본에서 해당 스피커는 지원되지 않습니다.

해결:

- `sohee` 또는 `dylan` 같은 지원 스피커로 바꿉니다.

### 2) `ffmpeg not found`

해결:

```bash
brew install ffmpeg
```

### 3) 마이크 녹음이 안 됨

해결:

- `시스템 설정 > 개인정보 보호 및 보안 > 마이크` 에서 터미널 권한 허용

### 4) 다운로드가 너무 오래 걸림

해결:

- 수업 시작 전에 미리 한 번 실행해서 모델을 받아두는 것이 가장 좋습니다.

### 5) tokenizer 관련 경고 문구가 뜸

예시:

- `incorrect regex pattern`
- `not supported for all configurations`

설명:

- 현재 설치 조합에서 실제 생성은 정상적으로 되지만, 실행 시 경고 문구가 보일 수 있습니다.
- `output_custom.wav` 또는 `merged.wav` 가 정상 생성되면 우선 계속 진행해도 됩니다.

## 12. 수업 시작용 최소 진행 순서

아래 순서만 그대로 진행하면 됩니다.

1. 터미널 열기
2. `brew install pyenv ffmpeg git`
3. `pyenv install 3.14.3`
4. 프로젝트 폴더로 이동
5. `python3 -m venv qwen-tts-env`
6. `source qwen-tts-env/bin/activate`
7. `pip install -r requirements-macos-lock.txt`
8. `python test.py`
9. `python tts_youtube_batch.py ...`

## 13. 수업용 추천 첫 데모 명령어

```bash
source qwen-tts-env/bin/activate
python tts_youtube_batch.py \
  --input script.txt \
  --outdir out_wavs_demo \
  --pipeline customvoice \
  --speaker sohee \
  --language Korean \
  --custom_instruct "따뜻하고 친근하게 읽어주세요" \
  --merge
```
