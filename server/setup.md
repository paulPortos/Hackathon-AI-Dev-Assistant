python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" for generating GITHUB_TOKEN_ENCRYPTION_KEY

Set Ollama Cloud credentials:

	export OLLAMA_API_KEY=your_ollama_cloud_key
	# OLLAMA_HOST is optional; omit to use the cloud default

Audio transcription still uses Gemini. If you need audio, set:

	export GOOGLE_API_KEY=your_google_api_key

Run the API with WebSocket support (port 8080 for WS):

	pip install -r requirements.txt
	DJANGO_SETTINGS_MODULE=config.settings daphne -b 0.0.0.0 -p 8080 config.asgi:application