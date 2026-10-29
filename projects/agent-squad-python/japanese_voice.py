"""ElevenLabs Japanese voice selection and pitch-preserving slow playback assets."""
import io
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import wave


def request(endpoint, payload=None):
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY is not configured")
    req = urllib.request.Request(
        "https://api.elevenlabs.io/" + endpoint,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            # Do not print the key, response body, or voice-library metadata.
            if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"ElevenLabs HTTP {exc.code}; check API key permissions, credits and model/voice access") from None
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise RuntimeError("ElevenLabs connection failed") from None
            time.sleep(5 * (attempt + 1))


def select_voice():
    configured = os.environ.get("ELEVENLABS_JAPANESE_VOICE_ID", "").strip()
    if configured:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", configured):
            raise ValueError("Invalid ElevenLabs voice ID")
        return configured
    # Only use licensed library/premade voices labelled as Japanese. Avoid
    # silently choosing a user's private cloned voice or an English default.
    voices = json.loads(request("v2/voices?language=ja&page_size=100&include_total_count=false"))
    candidates = [v for v in voices.get("voices", [])
                  if v.get("category") == "premade" or
                  (v.get("category") == "professional" and v.get("sharing", {}).get("status") == "enabled")]
    if not candidates:
        raise RuntimeError("Add a Japanese native-speaker voice to My Voices in ElevenLabs, then set ELEVENLABS_JAPANESE_VOICE_ID")
    candidates.sort(key=lambda v: (
        v.get("labels", {}).get("use_case") not in ("conversational", "conversation"),
        v.get("voice_id", ""),
    ))
    return candidates[0]["voice_id"]


def convert_audio(data, *, slow=False):
    executable = shutil.which("ffmpeg")
    if not executable:
        raise RuntimeError("ffmpeg is required for ElevenLabs audio conversion")
    args = [executable, "-hide_banner", "-loglevel", "error", "-i", "pipe:0"]
    if slow:
        # v4 has no speed slider. Time-stretch the same performance so the
        # slow track preserves its exact words, timbre and Japanese accent.
        args += ["-af", "atempo=0.78"]
    args += ["-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", "-f", "s16le", "pipe:1"]
    try:
        result = subprocess.run(args, input=data, capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError("Audio conversion could not complete") from None
    if result.returncode or not result.stdout:
        raise RuntimeError("ElevenLabs audio could not be decoded")
    # Write a seekable, correctly sized WAV header instead of ffmpeg's
    # streaming WAV header with an unknown frame count.
    output = io.BytesIO()
    with wave.open(output, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(24000)
        stream.writeframes(result.stdout)
    return output.getvalue()


def generate_pair(sentence):
    voice = select_voice()
    model = os.environ.get("ELEVENLABS_MODEL", "").strip() or "eleven_v4"
    encoded_voice = urllib.parse.quote(voice, safe="")
    audio = request(f"v1/text-to-speech/{encoded_voice}?output_format=mp3_44100_128", {
        "text": sentence,
        "model_id": model,
        "language_code": "ja",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    })
    normal = convert_audio(audio)
    slow = convert_audio(normal, slow=True)
    return normal, slow, {"tts_provider": "elevenlabs", "tts_model": model,
                          "tts_voice_id": voice, "slow_method": "pitch-preserving atempo=0.78"}
