# CLIP.LRU - Paste Before You Think.

![CLIP.LRU Logo](https://via.placeholder.com/150x50?text=CLIP.LRU) ![MIT License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-green.svg) ![React](https://img.shields.io/badge/React-18+-61dafb.svg)

CLIP.LRU is a next-generation clipboard management system that combines powerful sharing capabilities with intelligent LRU-based resource management. Store, organize and share content effortlessly across devices and teams.

## ✨ Key Features

### Core Functionalities
- **Multi-format Support** - Text, Markdown, images, videos, audio files and more
- **Smart Caching** - Automatic LRU-based cleanup with pinning capability
- **Secure Sharing** - Granular access controls (public/private/encrypted)
- **Anonymous Access** - Use without registration with configurable limits
- **Cross-platform** - Web-first with API for all your devices

### Advanced Capabilities
- **Streaming Uploads** - Progress tracking for large files
- **Multi-user Collaboration** - Share content with teams
- **Extensible Storage** - Local FS or custom backends
- **Activity Insights** - Usage analytics dashboard

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- MySQL 8.0+
- Node.js 18+
- Docker (optional)

### Installation
```bash
# Clone the repository
git clone https://github.com/zsuroy/lru-clip.git
cd lru-clip

# Backend setup
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

pip install -r requirements.txt

# Configuration
cp .env.example .env
# Edit .env with your MySQL database settings

# Initialize database
python scripts/init_db.py
```

### Running the Development Server
```bash
# Start backend server
python scripts/start_server.py

# Or manually:
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for API documentation.

## 🧩 Tech Stack
- **Backend**: FastAPI (Python 3.13+)
- **Frontend**: React 19 + TypeScript
- **UI**: Shadcn UI + TailwindCSS
- **Database**: MySQL
- **Auth**: JWT with OAuth2

## 📊 API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

Example API requests:

**Registered User:**
```bash
curl -X POST "http://localhost:8000/api/clips" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello World","clip_type":"text","access_level":"private"}'
```

**Anonymous User:**
```bash
# Create anonymous session
curl -X POST "http://localhost:8000/api/auth/anonymous"
# Returns: {"session_id": "abc123...", "user": {...}}

# Use session ID for requests
curl -X POST "http://localhost:8000/api/clips" \
  -H "X-Session-Id: abc123..." \
  -H "Content-Type: application/json" \
  -d '{"content":"Anonymous Hello","clip_type":"text","access_level":"public"}'
```

## 🔧 Configuration

Key environment variables:
```ini
# Database
DATABASE_URL=mysql://user:pass@localhost:3306/cliplru

# Storage
STORAGE_PATH=./uploads
MAX_FILE_SIZE=104857600

# Security
SECRET_KEY=your-secret-key
JWT_EXPIRE_MINUTES=1440

# Anonymous Users
ALLOW_ANONYMOUS=true
ANONYMOUS_MAX_CLIPS=100
ANONYMOUS_MAX_FILE_SIZE=10485760
ANONYMOUS_STORAGE_QUOTA=104857600
ANONYMOUS_CLIP_EXPIRE_HOURS=24
```

## 🧪 Testing

Run the test suite:
```bash
# Run all tests with coverage
python scripts/run_tests.py

# Run specific test file
python scripts/run_tests.py tests/test_auth.py

# Or manually:
pytest tests/ --cov=app --cov-report=html
```

## 🚢 Deployment

### Docker Compose
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contributing

We welcome contributions! Please see our [Contribution Guidelines](.github/CONTRIBUTING.md).

## 📜 License

GNU GPL V3 License - See [LICENSE](LICENSE) for details.
