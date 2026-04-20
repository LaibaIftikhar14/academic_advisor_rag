# backend/asr.py
import io
import os
import tempfile
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

print("Loading Whisper ASR model...")
asr_model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)
print("Whisper ASR model loaded ✅")


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Converts raw audio bytes to text.
    Handles webm/wav/ogg formats from browser.
    Uses temp file approach for reliable conversion.
    """
    try:
        # ── Save audio bytes to temp file ──
        # WHY TEMP FILE: faster-whisper works most
        # reliably with actual files not byte buffers
        with tempfile.NamedTemporaryFile(
            suffix=".webm",
            delete=False
        ) as tmp_input:
            tmp_input.write(audio_bytes)
            tmp_input_path = tmp_input.name

        # ── Convert webm → wav using ffmpeg ──
        tmp_output_path = tmp_input_path.replace(".webm", ".wav")

        os.system(
            f'ffmpeg -y -i "{tmp_input_path}" '
            f'-ar 16000 -ac 1 -c:a pcm_s16le '
            f'"{tmp_output_path}" -loglevel quiet'
        )

        # ── Transcribe the wav file ──
        segments, info = asr_model.transcribe(
            tmp_output_path,
            beam_size=5,
            language="en"
        )

        transcription = " ".join([
            segment.text for segment in segments
        ]).strip()

        # ── Cleanup temp files ──
        os.unlink(tmp_input_path)
        os.unlink(tmp_output_path)

        print(f"Transcribed: '{transcription}'")
        return transcription

    except Exception as e:
        print(f"ASR Error: {e}")
        return ""