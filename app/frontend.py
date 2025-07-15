"""
Frontend static file serving and routing configuration
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings

logger = logging.getLogger(__name__)


class FrontendConfig:
    """Frontend configuration and setup"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.web_dir = self._get_web_directory()
        self.static_dir = self._get_static_directory()
        
    def _get_web_directory(self) -> Optional[Path]:
        """Get the web directory path"""
        # Get the project root directory (parent of app directory)
        project_root = Path(__file__).parent.parent
        web_dir = project_root / "web"
        
        if web_dir.exists():
            logger.info(f"Web directory found: {web_dir}")
            return web_dir
        else:
            logger.warning(f"Web directory not found: {web_dir}")
            return None
    
    def _get_static_directory(self) -> Optional[Path]:
        """Get the static files directory"""
        if not self.web_dir:
            return None
            
        static_dir = self.web_dir / "static"
        if static_dir.exists():
            logger.info(f"Static directory found: {static_dir}")
            return static_dir
        else:
            logger.warning(f"Static directory not found: {static_dir}")
            return None
    
    def setup_static_files(self):
        """Setup static file serving"""
        if not self.web_dir:
            logger.warning("Web directory not available, skipping static file setup")
            return
        
        if self.static_dir:
            # Mount the web/static directory to /static
            self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")
            logger.info("Static files mounted from web/static directory")
        else:
            # Fallback: mount entire web directory
            self.app.mount("/static", StaticFiles(directory=str(self.web_dir)), name="static")
            logger.info("Static files mounted from web directory (fallback)")
    
    def setup_page_routes(self):
        """Setup frontend page routes"""
        if not self.web_dir:
            logger.warning("Web directory not available, skipping page routes setup")
            return
        
        # Main index page
        @self.app.get("/", include_in_schema=False)
        async def serve_index():
            """Serve the main index page"""
            return self._serve_html_file("index.html", "CLIP.LRU main page")
        
        # Shared clip page
        @self.app.get("/shared/{share_token}", include_in_schema=False)
        async def serve_shared_page(share_token: str):
            """Serve the shared clip page"""
            return self._serve_html_file("shared.html", "Shared clip page")
        
        # Debug page (only if enabled)
        if settings.enable_debug_pages:
            @self.app.get("/debug", include_in_schema=False)
            async def serve_debug_page():
                """Serve the debug page"""
                return self._serve_html_file("debug.html", "Debug page")

            logger.info("Debug page enabled at /debug")
        else:
            logger.info("Debug page disabled (set ENABLE_DEBUG_PAGES=true to enable)")

        # Test pages (only if enabled)
        if settings.enable_test_pages:
            @self.app.get("/tests/{test_name}", include_in_schema=False)
            async def serve_test_page(test_name: str):
                """Serve test pages"""
                # Validate test name to prevent directory traversal
                if not test_name.replace('_', '').replace('-', '').isalnum():
                    raise HTTPException(status_code=404, detail="Test page not found")

                test_file = f"tests/{test_name}.html"
                return self._serve_html_file(test_file, f"Test page: {test_name}")

            logger.info("Test pages enabled at /tests/*")
        else:
            logger.info("Test pages disabled (set ENABLE_TEST_PAGES=true to enable)")
        
        logger.info("Frontend page routes configured")
    
    def _serve_html_file(self, file_path: str, description: str) -> FileResponse:
        """Serve an HTML file with error handling"""
        if not self.web_dir:
            raise HTTPException(status_code=503, detail="Frontend not available")
        
        full_path = self.web_dir / file_path
        
        if full_path.exists() and full_path.is_file():
            logger.debug(f"Serving {description}: {full_path}")
            return FileResponse(str(full_path))
        else:
            logger.warning(f"{description} not found: {full_path}")
            raise HTTPException(status_code=404, detail=f"{description} not found")
    
    def setup(self):
        """Setup all frontend components"""
        logger.info("Setting up frontend components...")
        
        if not self.web_dir:
            logger.error("Frontend setup failed: web directory not found")
            return False
        
        try:
            self.setup_static_files()
            self.setup_page_routes()
            logger.info("Frontend setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Frontend setup failed: {e}")
            return False
    
    def get_info(self) -> dict:
        """Get frontend configuration information"""
        return {
            "web_directory": str(self.web_dir) if self.web_dir else None,
            "static_directory": str(self.static_dir) if self.static_dir else None,
            "available": self.web_dir is not None,
            "static_files_available": self.static_dir is not None,
            "debug_pages_enabled": settings.enable_debug_pages,
            "test_pages_enabled": settings.enable_test_pages,
        }


def setup_frontend(app: FastAPI) -> FrontendConfig:
    """Setup frontend for the FastAPI application"""
    frontend = FrontendConfig(app)
    frontend.setup()
    return frontend


# Additional utility functions for frontend management

def get_frontend_info() -> dict:
    """Get information about frontend availability"""
    project_root = Path(__file__).parent.parent
    web_dir = project_root / "web"
    static_dir = web_dir / "static"
    
    info = {
        "web_directory_exists": web_dir.exists(),
        "static_directory_exists": static_dir.exists(),
        "available_pages": [],
        "available_tests": []
    }
    
    if web_dir.exists():
        # Check for main pages
        main_pages = ["index.html", "shared.html", "debug.html"]
        for page in main_pages:
            if (web_dir / page).exists():
                info["available_pages"].append(page)
        
        # Check for test pages
        tests_dir = web_dir / "tests"
        if tests_dir.exists():
            for test_file in tests_dir.glob("*.html"):
                info["available_tests"].append(test_file.stem)
    
    return info


def validate_frontend_setup() -> tuple[bool, list[str]]:
    """Validate frontend setup and return status with issues"""
    issues = []
    
    project_root = Path(__file__).parent.parent
    web_dir = project_root / "web"
    
    if not web_dir.exists():
        issues.append("Web directory does not exist")
        return False, issues
    
    # Check required files
    required_files = [
        "index.html",
        "shared.html",
        "static/css/styles.css",
        "static/js/script.js"
    ]
    
    for file_path in required_files:
        full_path = web_dir / file_path
        if not full_path.exists():
            issues.append(f"Required file missing: {file_path}")
    
    # Check static directory structure
    static_dir = web_dir / "static"
    if static_dir.exists():
        required_dirs = ["css", "js"]
        for dir_name in required_dirs:
            dir_path = static_dir / dir_name
            if not dir_path.exists():
                issues.append(f"Required directory missing: static/{dir_name}")
    else:
        issues.append("Static directory does not exist")
    
    return len(issues) == 0, issues
