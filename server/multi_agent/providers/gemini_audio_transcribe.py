from django.conf import settings

from multi_agent.providers.audio_transcription_error import AudioTranscriptionError


def gemini_audio_transcribe(*, audio_bytes, content_type):
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise AudioTranscriptionError('Gemini audio transcription dependencies are not installed') from exc

    if not settings.GOOGLE_API_KEY:
        raise AudioTranscriptionError('GOOGLE_API_KEY is required for audio transcription')

    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        response = client.models.generate_content(
            model=settings.SR_DEV_STT_MODEL,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=content_type),
                'Transcribe this audio exactly. Return only the transcript text.',
            ],
        )
    except Exception as exc:
        raise AudioTranscriptionError('Gemini audio transcription failed') from exc

    transcript = str(getattr(response, 'text', '') or '').strip()
    if not transcript:
        raise AudioTranscriptionError('Gemini audio transcription returned an empty transcript')

    return transcript
