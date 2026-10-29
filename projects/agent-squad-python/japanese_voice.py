"""Google Cloud Chirp 3 HD Japanese synthesis with native pace control."""
import base64
import json
import os
import re
import time
import urllib.error
import urllib.request

DEFAULT_VOICE = "ja-JP-Chirp3-HD-Aoede"
_credentials = None


def access_token():
    """Use ADC supplied by the GitHub Google auth action, never an API key."""
    global _credentials
    try:
        import google.auth
        from google.auth.transport.requests import Request
        if _credentials is None:
            _credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not _credentials.valid:
            _credentials.refresh(Request())
        if not _credentials.token:
            raise RuntimeError("Empty Google Cloud OAuth token")
        return _credentials.token
    except Exception:
        # Credential exceptions can include private-key fragments or token data.
        raise RuntimeError("Google Cloud OAuth authentication failed; check GOOGLE_CLOUD_WIF_PROVIDER and GOOGLE_CLOUD_SERVICE_ACCOUNT repository variables and IAM trust") from None


def request(payload):
    token = access_token()
    req = urllib.request.Request(
        "https://texttospeech.googleapis.com/v1/text:synthesize",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            try:
                error = json.loads(exc.read()).get("error", {})
                message = error.get("message", "").replace(token, "[redacted]")[:1200]
            except (ValueError, AttributeError):
                message = "Check Cloud Text-to-Speech API enablement, billing and service account permissions"
            raise RuntimeError(f"Google Cloud TTS HTTP {exc.code}: {message}") from None
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise RuntimeError("Google Cloud TTS connection failed") from None
            time.sleep(5 * (attempt + 1))


def voice_name():
    name = os.environ.get("GOOGLE_CHIRP_VOICE", "").strip() or DEFAULT_VOICE
    if not re.fullmatch(r"ja-JP-Chirp3-HD-[A-Za-z]+", name):
        raise ValueError("GOOGLE_CHIRP_VOICE must be a ja-JP-Chirp3-HD voice")
    return name


def generate_pair(sentence):
    voice = voice_name()
    tracks = []
    for rate in (1.0, 0.75):
        result = request({
            "input": {"text": sentence},
            "voice": {"languageCode": "ja-JP", "name": voice},
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000,
                            "speakingRate": rate},
        })
        encoded = result.get("audioContent")
        if not encoded:
            raise RuntimeError("Chirp 3 HD returned no audio")
        # Cloud TTS LINEAR16 includes its WAV header.
        tracks.append(base64.b64decode(encoded, validate=True))
    return tracks[0], tracks[1], {
        "tts_provider": "google-cloud", "tts_model": "chirp-3-hd",
        "tts_voice_id": voice, "slow_method": "native speakingRate=0.75",
    }
