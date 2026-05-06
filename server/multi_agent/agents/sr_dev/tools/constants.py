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
MAX_TREE_RESULTS = 120
MAX_COMPARE_FILES = 80
MAX_COMPARE_COMMITS = 25
DEPENDENCY_MANIFEST_FILENAMES = {
    'Cargo.toml',
    'Gemfile',
    'go.mod',
    'package-lock.json',
    'package.json',
    'pnpm-lock.yaml',
    'poetry.lock',
    'Pipfile',
    'Pipfile.lock',
    'pom.xml',
    'pyproject.toml',
    'requirements.txt',
    'yarn.lock',
}
SENSITIVE_FILENAME_PREFIXES = {
    '.env',
}
SENSITIVE_FILENAME_SUFFIXES = {
    '.key',
    '.pem',
    '.p12',
    '.pfx',
}
SENSITIVE_FILENAME_KEYWORDS = {
    'credential',
    'credentials',
    'private-key',
    'private_key',
    'secret',
    'secrets',
    'service-account',
    'service_account',
}
