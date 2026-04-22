from __future__ import annotations

import base64
import io
import wave

from openai import NotFoundError, OpenAI

from config import (
    TTS_API_KEY,
    TTS_BASE_URL,
    TTS_MODEL,
    TTS_RESPONSE_FORMAT,
    TTS_VOICE,
)


class TTSService:
    def __init__(self):
        self.api_key = TTS_API_KEY
        self.base_url = (TTS_BASE_URL or "").strip()

    @staticmethod
    def _candidate_base_urls(base_url: str) -> list[str]:
        base = base_url.rstrip("/")
        if not base:
            return []
        urls = [base]
        if base.endswith("/v1"):
            urls.append(base[:-3].rstrip("/"))
        else:
            urls.append(f"{base}/v1")
        # de-duplicate while preserving order
        out = []
        for u in urls:
            if u and u not in out:
                out.append(u)
        return out

    @staticmethod
    def _pcm16_to_wav_bytes(pcm_bytes: bytes, sample_rate: int = 24000) -> bytes:
        bio = io.BytesIO()
        with wave.open(bio, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # PCM16LE
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_bytes)
        return bio.getvalue()

    def synthesize(self, text: str) -> tuple[bytes, str]:
        text = (text or "").strip()
        if not text:
            raise ValueError("text is required")
        if not self.api_key or self.api_key == "replace-with-your-tts-api-key":
            raise ValueError("TTS_API_KEY is not configured")

        tried_urls: list[str] = []
        last_error: Exception | None = None
        for base_url in self._candidate_base_urls(self.base_url):
            tried_urls.append(base_url)
            try:
                client = OpenAI(api_key=self.api_key, base_url=base_url)
                # Xiaomi Mimo sample uses chat.completions + audio with streaming chunks.
                completion = client.chat.completions.create(
                    model=TTS_MODEL,
                    messages=[{"role": "assistant", "content": text}],
                    audio={"format": TTS_RESPONSE_FORMAT, "voice": TTS_VOICE},
                    stream=True,
                )

                audio_bytes = bytearray()
                for chunk in completion:
                    if not getattr(chunk, "choices", None):
                        continue
                    delta = chunk.choices[0].delta
                    audio = getattr(delta, "audio", None)
                    if not audio:
                        continue
                    if isinstance(audio, dict):
                        b64_data = audio.get("data")
                    else:
                        b64_data = getattr(audio, "data", None)
                    if b64_data:
                        audio_bytes.extend(base64.b64decode(b64_data))

                if not audio_bytes:
                    raise RuntimeError("TTS returned no audio data")

                fmt = (TTS_RESPONSE_FORMAT or "").lower()
                if fmt in ("pcm16", "pcm"):
                    return self._pcm16_to_wav_bytes(bytes(audio_bytes)), "audio/wav"

                media_type_map = {
                    "mp3": "audio/mpeg",
                    "wav": "audio/wav",
                    "opus": "audio/ogg",
                    "aac": "audio/aac",
                    "flac": "audio/flac",
                }
                return bytes(audio_bytes), media_type_map.get(fmt, "application/octet-stream")
            except NotFoundError as exc:
                last_error = exc
                continue
            except Exception as exc:
                last_error = exc
                break

        tried = ", ".join(tried_urls) if tried_urls else "<empty>"
        raise RuntimeError(f"TTS request failed. Tried base URLs: {tried}. Last error: {last_error}")
