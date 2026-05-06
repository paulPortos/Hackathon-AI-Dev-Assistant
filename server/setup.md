python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" for generating GITHUB_TOKEN_ENCRYPTION_KEY

Set Ollama Cloud credentials:

	# Linux/macOS
	export OLLAMA_API_KEY=your_ollama_cloud_key
	# Windows (PowerShell)
	$env:OLLAMA_API_KEY="your_ollama_cloud_key"

Run the API with WebSocket support (port 8080 for WS):

	pip install -r requirements.txt
	
	# Linux/macOS
	DJANGO_SETTINGS_MODULE=config.settings daphne -b 0.0.0.0 -p 8080 config.asgi:application
	
	# Windows (PowerShell)
	$env:DJANGO_SETTINGS_MODULE="config.settings"; daphne -b 0.0.0.0 -p 8080 config.asgi:application
	
	# Note: DJANGO_SETTINGS_MODULE defaults to 'config.settings' in asgi.py, 
	# so you can also just run:
	daphne -b 0.0.0.0 -p 8080 config.asgi:application

