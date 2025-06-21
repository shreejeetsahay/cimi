# docker-compose.yml
version: '3.8'

services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    volumes:
      - ./api:/app
      - ./database:/app/database
    environment:
      - DATABASE_URL=sqlite:///./database/chatcards.db
    depends_on:
      - database

  dashboard:
    build: ./dashboard
    ports:
      - "3000:3000"
    volumes:
      - ./dashboard:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  database:
    image: alpine:latest
    volumes:
      - ./database:/data
    command: tail -f /dev/null  # Keep container running

# .gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.pytest_cache/
*.egg-info/
.installed.cfg
*.egg

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.eslintcache

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build outputs
dist/
build/
*.crx
*.pem

# Vector databases
*.faiss
*.index