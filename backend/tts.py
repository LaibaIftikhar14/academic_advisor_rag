# backend/tts.py
import io
import wave
import re
from piper.voice import PiperVoice

MODEL_PATH = "../models/en_US-amy-medium.onnx"

print("Loading Piper TTS model...")
tts_model = PiperVoice.load(MODEL_PATH)
print("Piper TTS model loaded ✅")
print(f"Sample rate: {tts_model.config.sample_rate}")


def text_to_speech(text: str) -> bytes:
    """
    Converts text to WAV audio bytes.
    Uses synthesize_wav() with correct sample rate.
    """
    try:
        buf = io.BytesIO()

        with wave.open(buf, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(tts_model.config.sample_rate)
            tts_model.synthesize_wav(text, wav_file)

        buf.seek(0)
        audio_bytes = buf.read()
        print(f"TTS generated {len(audio_bytes)} bytes ✅")
        return audio_bytes

    except Exception as e:
        print(f"TTS Error: {e}")
        import traceback
        traceback.print_exc()
        return b""


def clean_text_for_speech(text: str) -> str:
    """Cleans text before sending to TTS."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub("", text)
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+\s', '', text)
    text = re.sub(r'`+', '', text)
    text = " ".join(text.split())
    return text.strip()