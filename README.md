# CLIP.LRU - Paste Before You Think

![GPL License](https://img.shields.io/badge/license-GPL-blue.svg) ![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg) ![Vanilla JS](https://img.shields.io/badge/Frontend-Vanilla%20JS-yellow.svg)

A modern, full-featured clipboard and file sharing application built with FastAPI and vanilla JavaScript. Share text, files, and create secure clips with password protection and anonymous access support.

## ✨ Features

### 📋 Clipboard Management
- **Text Clips**: Store and organize text snippets with rich formatting
- **Quick Access**: Fast search and filtering capabilities
- **Bulk Operations**: Select and manage multiple clips at once
- **Auto-expiration**: Configurable clip expiration times

### 📁 Advanced File Sharing
- **Multi-File Upload**: Upload multiple files simultaneously with drag & drop
- **Progress Tracking**: Real-time upload progress with detailed feedback
- **File Management**: Preview, download, and organize uploaded files
- **All File Types**: Support for any file type with MIME detection

### 🔒 Security & Access Control
- **Three Access Levels**: Private, public, and password-protected clips
- **Secure Encryption**: Password-protected clips with robust security
- **Anonymous Support**: Full functionality without registration required
- **Secure Sharing**: Unique, non-guessable share tokens

### 🌐 Modern Web Interface
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Vanilla JavaScript**: No framework dependencies, fast and lightweight
- **Clean UI**: Modern, intuitive interface with excellent UX
- **Progressive Enhancement**: Graceful degradation for all browsers

### 🛠️ Developer Features
- **Complete REST API**: Full RESTful API with OpenAPI documentation
- **Comprehensive Testing**: 85+ tests with high coverage
- **Development Tools**: Built-in debug pages and testing utilities
- **Modular Architecture**: Easy to extend and customize

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+** (Python 3.13 recommended)
- **pip** for dependency management

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/zsuroy/lru-clip.git
cd lru-clip
```

2. **Create virtual environment (recommended):**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment (optional):**
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

5. **Run the application:**
```bash
python -m uvicorn app.main:app --reload --port 8000
```

6. **Access the application:**
   - **Web Interface**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Alternative API Docs**: http://localhost:8000/redoc

## ⚙️ Configuration

### Environment Variables

Configure the application using environment variables or a `.env` file:

```env
# Database Configuration
DATABASE_URL=sqlite:///./cliplru.db

# Security Settings
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Storage
STORAGE_PATH=./uploads
MAX_FILE_SIZE=52428800  # 50MB in bytes
ALLOWED_FILE_TYPES=*    # * for all types, or comma-separated list

# Anonymous User Settings
ALLOW_ANONYMOUS=true
ANONYMOUS_MAX_CLIPS=100
ANONYMOUS_MAX_FILE_SIZE=10485760  # 10MB
ANONYMOUS_STORAGE_QUOTA=104857600  # 100MB
ANONYMOUS_CLIP_EXPIRE_HOURS=24

# Development & Testing (set to true to enable)
DEBUG=false
```

### Configuration Examples

#### Production Setup
```env
DATABASE_URL=mysql://user:password@localhost/cliplru
SECRET_KEY=your-production-secret-key
STORAGE_PATH=/var/lib/cliplru/uploads
ALLOW_ANONYMOUS=false
```

#### Development Setup
```env
DATABASE_URL=sqlite:///./dev.db
SECRET_KEY=dev-secret-key
STORAGE_PATH=./dev_uploads
ALLOW_ANONYMOUS=true
DEBUG=true
```

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with Python 3.13+
- **Database**: SQLite (default) or MySQL
- **Authentication**: JWT tokens + Anonymous sessions
- **Storage**: Local filesystem with configurable path
- **API**: RESTful with automatic OpenAPI documentation

### Frontend (Vanilla JavaScript)
- **No Framework**: Pure JavaScript for maximum compatibility
- **Modern ES6+**: Uses modern JavaScript features with fallbacks
- **Responsive CSS**: Mobile-first responsive design
- **Progressive Enhancement**: Works without JavaScript enabled
- **File Upload**: Advanced multi-file upload with progress tracking

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Frontend Status**: http://localhost:8000/api/frontend/status

### Example API Usage

#### Anonymous User Workflow
```bash
# 1. Create anonymous session
curl -X POST "http://localhost:8000/api/auth/anonymous"
# Returns: {"session_id": "abc123...", "user": {...}}

# 2. Upload a file
curl -X POST "http://localhost:8000/api/files/upload" \
  -H "X-Session-Id: abc123..." \
  -F "file=@example.txt"

# 3. Create a clip with the file
curl -X POST "http://localhost:8000/api/clips/" \
  -H "X-Session-Id: abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My File Clip",
    "content": "Description of the file",
    "clip_type": "file",
    "access_level": "public",
    "file_ids": [1]
  }'
```

#### Registered User Workflow
```bash
# 1. Register or login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# 2. Create encrypted clip
curl -X POST "http://localhost:8000/api/clips/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Secret Clip",
    "content": "This is secret content",
    "clip_type": "text",
    "access_level": "encrypted",
    "password": "secret123"
  }'
```

## 🧪 Development & Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage report
python -m pytest --cov=app --cov-report=html

# Run specific test categories
python -m pytest tests/test_sharing.py -v
python -m pytest tests/test_file_permissions.py -v

# Run tests without warnings
python -m pytest --disable-warnings
```

### Testing Pages (when enabled)

Set `ENABLE_TEST_PAGES=true` in your environment to access:
- **File Upload Tests**: http://localhost:8000/tests/test_file_upload
- **Sharing Tests**: http://localhost:8000/tests/test_sharing
- **Debug Tools**: http://localhost:8000/debug (requires `ENABLE_DEBUG_PAGES=true`)

## 📁 Project Structure

```
lru-clip/
├── app/                          # Main application
│   ├── main.py                   # FastAPI application entry point
│   ├── config.py                 # Configuration management
│   ├── frontend.py               # Frontend integration
│   ├── database.py               # Database configuration
│   ├── models/                   # SQLAlchemy models
│   ├── schemas/                  # Pydantic schemas
│   ├── routers/                  # API route handlers
│   └── services/                 # Business logic
├── web/                          # Frontend files
│   ├── static/
│   │   ├── css/styles.css        # Main stylesheet
│   │   └── js/script.js          # Main JavaScript
│   ├── tests/                    # Frontend test pages
│   ├── index.html                # Main application page
│   ├── shared.html               # Shared clip viewer
├── tests/                        # Backend tests (85+ tests)
├── scripts/                      # Utility scripts
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🚢 Deployment

### Simple Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set production environment
export DATABASE_URL=mysql://user:pass@localhost/cliplru
export SECRET_KEY=your-production-secret
export STORAGE_PATH=/var/lib/cliplru/uploads

# Run with Gunicorn
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

#### Quick Start with Docker

```bash

# Deploy Helper
./docker/deploy.sh

# Deploy with SQLite (lightweight, good for development)
./docker/deploy.sh sqlite

# Or deploy with MySQL (production-ready)
./docker/deploy.sh mysql

# Access the application at http://localhost:8000
```

#### Available deployment options:
- **SQLite deployment**: `docker-compose.yml` - Simple, file-based database
- **MySQL deployment**: `docker-compose.mysql.yml` - Production-ready with MySQL 8.0

For detailed Docker deployment instructions, see [docker/README.md](docker/README.md).

## 🤝 Contributing

We welcome contributions! Please see our [Contribution Guidelines](.github/CONTRIBUTING.md).

## 📄 License

This project is licensed under the GPL V3 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- Frontend uses vanilla JavaScript for maximum compatibility and performance
- Database support via [SQLAlchemy](https://sqlalchemy.org/)
- Testing with [pytest](https://pytest.org/) - 85+ tests with high coverage
- UI design inspired by modern web applications

---

**CLIP.LRU** - Making clipboard and file sharing simple, secure, and efficient. 🚀
