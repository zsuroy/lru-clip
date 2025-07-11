# CLIP.LRU - Paste Before You Think.

![CLIP.LRU Logo](https://via.placeholder.com/150x50?text=CLIP.LRU) ![MIT License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-green.svg) ![React](https://img.shields.io/badge/React-18+-61dafb.svg)

CLIP.LRU is a next-generation clipboard management system that combines powerful sharing capabilities with intelligent LRU-based resource management. Store, organize and share content effortlessly across devices and teams.

## ✨ Key Features

### Core Functionalities
- **Multi-format Support** - Text, Markdown, images, videos, audio files and more
- **Smart Caching** - Automatic LRU-based cleanup with pinning capability
- **Secure Sharing** - Granular access controls (public/private/encrypted)
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

# Frontend setup
cd frontend
npm install
npm run build
cd ..

# Configuration
cp .env.example .env
# Edit .env with your settings
```

### Running the Development Server
```bash
# Start backend
uvicorn app.main:app --reload

# In another terminal, start frontend
cd frontend
npm run dev
```

Visit `http://localhost:3000` in your browser.

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

Example API request:
```bash
curl -X POST "http://localhost:8000/api/clips" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello World","type":"text","is_pinned":false}'
```

## 🔧 Configuration

Key environment variables:
```ini
# Database
DATABASE_URL=mysql://user:pass@localhost:3306/cliplru

# Storage
STORAGE_TYPE=local  # or 's3'
STORAGE_PATH=./uploads

# Security
SECRET_KEY=your-secret-key
JWT_EXPIRE_MINUTES=1440
```

## 🧪 Testing

Run the test suite:
```bash
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
