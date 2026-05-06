DEFAULT_SEARCH_EXTENSIONS = {
    '.css',
    '.go',
    '.html',
    '.java',
    '.js',
    '.json',
    '.jsx',
    '.md',
    '.py',
    '.rb',
    '.rs',
    '.sql',
    '.ts',
    '.tsx',
    '.txt',
    '.yaml',
    '.yml',
}
ALWAYS_INCLUDE_FILENAMES = {
    '.env',
    '.env.example',
    'Dockerfile',
    'Makefile',
    'Procfile',
    'docker-compose.yml',
    'docker-compose.yaml',
}
MAX_READ_FILE_BYTES = 100_000
MAX_SEARCH_FILE_BYTES = 200_000
MAX_SEARCH_RESULTS = 20
MAX_TREE_FILES_TO_SCAN = 40
SEARCH_SNIPPET_CONTEXT_LINES = 2
SEARCH_SNIPPET_MAX_CHARS = 700
