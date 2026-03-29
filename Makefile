PYTHON := .venv/bin/python

.PHONY: setup test demo clone-help

setup:
	bash scripts/setup_macos.sh

test:
	$(PYTHON) test.py

demo:
	$(PYTHON) tts_youtube_batch.py \
		--input script.txt \
		--outdir out_wavs_demo \
		--pipeline customvoice \
		--speaker sohee \
		--language Korean \
		--custom_instruct "따뜻하고 친근하게 읽어주세요" \
		--merge

clone-help:
	@echo "사용 예시:"
	@echo ".venv/bin/python clone_example.py --ref-audio ./ref.wav --ref-text '안녕하세요. 제 목소리 샘플입니다.'"
