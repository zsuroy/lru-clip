#!/bin/bash

# 🚀 CLIP.LRU Docker Deployment Script
# 📦 This script helps you deploy CLIP.LRU using Docker Compose
#
# 👨‍💻 Author: @Suroy (https://suroy.cn)
# 🌐 Repository: https://github.com/zsuroy/lru-clip
# 📅 Last Updated: $(date +%Y-%m-%d)

set -e

# 🔍 Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DOCKER_DIR="${SCRIPT_DIR}"

# 📍 Change to docker directory for docker-compose commands
cd "${DOCKER_DIR}"

# Constants
ENV_FILE="${PROJECT_ROOT}/.env"


# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[ℹ️ INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✅ SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠️ WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[❌ ERROR]${NC} $1"
}

# 🔍 Check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "🐳 Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "🐳 Docker daemon is not running. Please start Docker."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "🐙 Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi

    print_success "🐳 Docker and Docker Compose are available"
}

# 📖 Show usage information
show_usage() {
    echo "🚀 CLIP.LRU Docker Deployment Script"
    echo "🕹 Author: @Suroy (https://suroy.cn)"
    echo ""
    echo "📋 Usage: $0 [OPTION]"
    echo ""
    echo "🎯 Options:"
    echo "  sqlite    🗃 Deploy with SQLite database (lightweight, default)"
    echo "  mysql     🐬 Deploy with MySQL database (production)"
    echo "  stop      🛑 Stop all services"
    echo "  clear     🗑 Stop and clear all services"
    echo "  restart   🔄 Restart all services"
    echo "  logs      📝 Show logs"
    echo "  status    📊 Show service status"
    echo "  help      ❓ Show this help message"
    echo ""
    echo "💡 Examples:"
    echo "  $0 sqlite     # 🗃 Deploy with SQLite"
    echo "  $0 mysql      # 🐬 Deploy with MySQL"
    echo "  $0 stop       # 🛑 Stop all services"
    echo "  $0 logs       # 📝 Show logs"
}

# 🗃️ Deploy with SQLite
deploy_sqlite() {
    print_info "🚀 Deploying CLIP.LRU with SQLite database..."

    # Create necessary directories
    mkdir -p "${PROJECT_ROOT}/data" "${PROJECT_ROOT}/uploads"

    # Copy environment file if it doesn't exist
    if [ ! -f "${PROJECT_ROOT}/.env" ]; then
        print_info "📄 Creating .env file from template..."
        if [ -f "${PROJECT_ROOT}/.env.example" ]; then
            cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
            print_warning "📝 Please review and update .env file with your settings"
        fi
    fi

    # Generate secure JWT secret if using default
    generate_jwt_secret

    # Default env file
    local env_flag=""
    if [ -f "$ENV_FILE" ]; then
        echo "🥖 Load env file $ENV_FILE"
        env_flag="--env-file=$ENV_FILE"
    else
        echo "⚠️ Unable to find $ENV_FILE file [default]"
    fi

    # Deploy
    docker-compose "${env_flag}" up -d --build

    print_success "CLIP.LRU deployed with SQLite!"
    print_info "🌐 Access the application at: http://localhost:8000"
    print_info "📚 API documentation at: http://localhost:8000/docs"
}

# Deploy with MySQL
deploy_mysql() {
    print_info "🐬 Deploying CLIP.LRU with MySQL database..."

    # Create necessary directories
    mkdir -p "${PROJECT_ROOT}/uploads"

    # Copy environment file if it doesn't exist
    if [ ! -f "${PROJECT_ROOT}/.env" ]; then
        print_info "Creating .env file from template..."
        if [ -f "${PROJECT_ROOT}/.env.example" ]; then
            cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"            
            print_warning "Please review and update .env file with your MySQL settings"
        else
            print_warning ".env.example template not found. Please create .env file manually."
        fi
    fi

    # Generate secure MySQL secret if using defaults
    generate_mysql_secret

    # Generate secure JWT secret if using default
    generate_jwt_secret

    # Default env file
    local env_flag
    if [ -f "$ENV_FILE" ]; then
        echo "🥖 Load env file $ENV_FILE"
        env_flag="--env-file=$ENV_FILE"
    else
        env_flag=""
        echo "⚠️ Unable to find $ENV_FILE file [default]"
    fi

    # Deploy
    docker-compose -f docker-compose.mysql.yml "${env_flag}" up -d --build

    print_success "CLIP.LRU deployed with MySQL!"
    print_info "🌐 Access the application at: http://localhost:8000"
    print_info "📚 API documentation at: http://localhost:8000/docs"
    print_info "🐬 MySQL is available at: localhost:3306"
}

# 🔧 Helper function to update or add environment variables
update_env_var() {
    local env_file="${PROJECT_ROOT}/.env"
    local var_name="$1"
    local var_value="$2"

    # Escape special characters in the value for sed
    local escaped_value
    escaped_value=$(printf '%s\n' "$var_value" | sed -e 's/[\/&]/\\&/g')

    # Check if the variable already exists in the file
    if grep -q "^${var_name}=" "$env_file"; then
        # Update the existing variable
        sed -i.bak "s/^${var_name}=.*/${var_name}=${escaped_value}/" "$env_file"
        print_info "🔄 Updated ${var_name} in .env file"
    else
        # Add new variable
        echo "${var_name}=${escaped_value}" >> "$env_file"
        print_info "🆕 Added ${var_name} to .env file"
    fi

    # Remove backup file if it exists
    rm -f "$env_file.bak" 2>/dev/null
}

# generate database URL based on current configuration
generate_database_url() {
    local db_type="${1:-mysql}"  # Default to mysql if not specified
    local env_file="${PROJECT_ROOT}/.env"

    case "$db_type" in
        mysql)
            local mysql_user
            local mysql_password
            local mysql_database
            local db_url
            mysql_user=$(grep "^DB_USER=" "$env_file" | cut -d'=' -f2)
            mysql_password=$(grep "^DB_PASSWORD=" "$env_file" | cut -d'=' -f2)
            mysql_database=$(grep "^DB_DATABASE=" "$env_file" | cut -d'=' -f2)
            db_url="mysql://${mysql_user}:${mysql_password}@mysql:3306/${mysql_database}"
            ;;
        sqlite)
            local db_url="sqlite:///./data/cliplru.db"
            ;;
        *)
            print_error "Unsupported database type: $db_type"
            exit 1
            ;;
    esac

    update_env_var "DATABASE_URL" "$db_url"
    print_info "Generated DATABASE_URL for $db_type: $db_url"
}

# Generate secure MySQL credentials if using defaults
generate_mysql_secret() {
    local env_file="${PROJECT_ROOT}/.env"
    local needs_update=false

    # Create .env if it doesn't exist
    [ -f "$env_file" ] || touch "$env_file"

    # Ensure required MySQL variables are set
    update_env_var "DB_USER" "cliplru"
    update_env_var "DB_DATABASE" "cliplru"

    # Check and update MySQL app password
    if ! grep -q "DB_PASSWORD=" "$env_file" || grep -q "DB_PASSWORD=cliplru_password" "$env_file"; then
        print_info "Generating secure MySQL app password..."
        local app_password
        app_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        update_env_var "DB_PASSWORD" "$app_password"
        print_warning "MySQL App password: $app_password"
        needs_update=true
    fi

    # Generate MySQL database URL
    generate_database_url "mysql"

    if [ "$needs_update" = true ]; then
        print_success "MySQL credentials generated and saved to .env"
        print_info "Please save these credentials securely!"
    else
        print_info "MySQL credentials already configured securely"
    fi
}

# Generate JWT secret for deployment
generate_jwt_secret() {
    local env_file="${PROJECT_ROOT}/.env"

    if [ -f "$env_file" ] && grep -q "SECRET_KEY=your-super-secret-key-change-this-in-production-please" "$env_file"; then
        print_info "Generating secure JWT secret key..."
        local secret_key
        secret_key=$(openssl rand -base64 64 | tr -dc '[:alnum:]' | cut -c1-50)
        update_env_var "SECRET_KEY" "$secret_key"
        print_warning "JWT Secret key: $secret_key"
        print_success "Secure JWT secret generated"
    fi
}

# Switch database configuration
switch_database() {
    local db_type="${1:-mysql}"

    case "$db_type" in
        mysql)
            generate_mysql_secret
            ;;
        sqlite)
            generate_database_url "sqlite"
            print_success "Switched to SQLite database configuration"
            ;;
        *)
            print_error "Unsupported database type: $db_type"
            print_info "Usage: $0 switch-database [mysql|sqlite]"
            exit 1
            ;;
    esac
}

# Stop services
stop_services() {
    print_info "Stopping CLIP.LRU services..."
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.mysql.yml down 2>/dev/null || true
    print_success "Services stopped"
}

# Stop services
clear_services() {
    print_info "Stopping CLIP.LRU services..."
    docker-compose down --rmi all --volumes --remove-orphans 2>/dev/null || true
    docker-compose -f docker-compose.mysql.yml down --rmi all --volumes --remove-orphans 2>/dev/null || true
    print_success "Services stopped and cleared"
}

# Show logs
show_logs() {
    if docker-compose ps | grep -q "clip-lru"; then
        docker-compose logs -f
    elif docker-compose -f docker-compose.mysql.yml ps | grep -q "clip-lru"; then
        docker-compose -f docker-compose.mysql.yml logs -f
    else
        print_warning "No CLIP.LRU services are running"
    fi
}

# Show status
show_status() {
    print_info "📊 CLIP.LRU Service Status:"
    echo ""
    
    if docker-compose ps | grep -q "clip-lru"; then
        print_info "🥤 All deployments:"
        docker-compose ps
    else
        print_warning "No CLIP.LRU services are running"
    fi
}

# Main script logic
main() {
    case "${1:-help}" in
        sqlite)
            check_docker
            deploy_sqlite
            ;;
        mysql)
            check_docker
            deploy_mysql
            ;;
        stop)
            stop_services
            ;;
        clear)
            clear_services
            ;;
        restart)
            stop_services
            sleep 2
            deploy_sqlite
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
