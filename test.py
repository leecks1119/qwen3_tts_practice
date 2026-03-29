import soundfile as sf
from mlx_audio.tts.utils import load_model

# 모델 로드 (첫 실행 시 자동 다운로드 ~4.5GB)
model = load_model("mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16")

# 현재 설치본에서 확인된 한국어 사용 가능 스피커는 `sohee`입니다.
speaker = "sohee"

# 한국어 TTS 생성
results = list(model.generate_custom_voice(
    text="안녕하세요, 큐웬 TTS 테스트입니다. 오늘 날씨가 정말 좋네요!",
    speaker=speaker,
    language="Korean",
    instruct="따뜻하고 친근한 톤으로 말해주세요",
))

# WAV 저장
audio = results[0].audio
sf.write("output_custom.wav", audio, 24000)
print("✅ 생성 완료!")
