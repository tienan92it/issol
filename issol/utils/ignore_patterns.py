IGNORE_PATTERNS = [
    # Common version control
    ".git*",
    ".svn*",
    ".hg*",

    # Node.js
    "node_modules*",
    "npm-debug.log*",
    "yarn-debug.log*",
    "yarn-error.log*",
    "package-lock.json",
    "yarn.lock",

    # Python
    "__pycache__*",
    "*.py[cod]",
    "*.so",
    ".Python",
    "build*",
    "develop-eggs*",
    "dist*",
    "downloads*",
    "eggs*",
    ".eggs*",
    "lib*",
    "lib64*",
    "parts*",
    "sdist*",
    "var*",
    "wheels*",
    "*.egg-info*",
    ".installed.cfg",
    "*.egg",
    "venv*",
    "ENV*",
    "pip-log.txt",
    "pip-delete-this-directory.txt",
    "Pipfile.lock",

    # Ruby
    "Gemfile.lock",

    # Java
    "*.class",
    "*.log",
    "*.jar",
    "*.war",
    "*.nar",
    "*.ear",
    "*.zip",
    "*.tar.gz",
    "*.rar",
    "hs_err_pid*",

    # Gradle
    ".gradle*",
    "build*",

    # Maven
    "target*",
    "pom.xml.tag",
    "pom.xml.releaseBackup",
    "pom.xml.versionsBackup",
    "pom.xml.next",
    "release.properties",
    "dependency-reduced-pom.xml",
    "buildNumber.properties",
    ".mvn/timing.properties",

    # IDEs and editors
    ".idea*",
    ".vscode*",
    "*.swp",
    "*.swo",
    "*~",
    "*.sublime-workspace",

    # OS generated
    ".DS_Store",
    ".DS_Store?",
    "._*",
    ".Spotlight-V100",
    ".Trashes",
    "ehthumbs.db",
    "Thumbs.db",

    # Logs
    "logs*",
    "*.log",

    # Environment variables and secrets
    ".env*",
    "*.pem",
    "*.key",
    "*.crt",

    # Build outputs
    "dist*",
    "out*",

    # Dependency directories
    "jspm_packages*",
    "bower_components*",

    # Coverage directories
    "coverage*",
    ".nyc_output*",

    # Grunt intermediate storage
    ".grunt*",

    # Docker
    "docker-compose.override.yml",

    # Other common ignore patterns
    "*.bak",
    "*.tmp",
    "*.temp",
    "*.swp",
    "*.cache",
    "*.patch",
    "*.diff",
    "*.orig",

    # Specific to certain build tools or frameworks
    ".next*",  # Next.js
    ".nuxt*",  # Nuxt.js
    ".netlify*",  # Netlify
    ".serverless*",  # Serverless Framework
    ".fusebox*",  # FuseBox
    ".dynamodb*",  # DynamoDB Local
    ".tern-port",  # Tern

    # Microsoft Office temporary files
    "~$*"
]