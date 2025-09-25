# PostgreSQL Migration Guide

This guide explains how to migrate your Home Money Management app from SQLite to PostgreSQL using Docker containers.

## 🎯 What Changed

### 1. **Database Engine**

- **Before**: SQLite (file-based database)
- **After**: PostgreSQL (containerized database)

### 2. **Dependencies**

- Added `psycopg2-binary==2.9.9` to `requirements.txt`
- Updated Dockerfile with PostgreSQL development libraries

### 3. **Configuration**

- Django settings now support both SQLite (local dev) and PostgreSQL (Docker)
- Environment variables for database configuration
- Health checks for PostgreSQL container

### 4. **Docker Setup**

- New PostgreSQL container with persistent volume
- Proper service dependencies and health checks
- Environment variables for database connection

## 🚀 Quick Start

### 1. **Stop Current Containers**

```bash
docker-compose down
```

### 2. **Remove Old SQLite Database (Optional)**

```bash
# This will remove your existing data - backup first if needed
rm API/db.sqlite3
```

### 3. **Start with PostgreSQL**

```bash
docker-compose up --build
```

### 4. **Verify Migration**

- Check that PostgreSQL container is running: `docker ps`
- Check Django logs for successful database connection
- Access your app at `http://localhost:8080`

## 📊 Database Configuration

### **Environment Variables**

The app now uses these environment variables for database configuration:

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `DATABASE_URL` | - | Full PostgreSQL connection string |
| `POSTGRES_DB` | `moneymanagement` | Database name |
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `POSTGRES_HOST` | `postgres` | Database host (container name) |
| `POSTGRES_PORT` | `5432` | Database port |

### **Django Settings Logic**

```python
# Automatically chooses database based on environment
if os.getenv('DATABASE_URL'):
    # Use PostgreSQL (Docker/Production)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            # ... PostgreSQL configuration
        }
    }
else:
    # Use SQLite (Local Development)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
```

## 🔧 Development Workflow

### **Local Development (SQLite)**

```bash
# Run locally with SQLite
cd API
python manage.py runserver
```

### **Docker Development (PostgreSQL)**

```bash
# Run with PostgreSQL container
docker-compose up
```

### **Database Migrations**

```bash
# In Docker environment
docker-compose exec money-management-api python manage.py makemigrations
docker-compose exec money-management-api python manage.py migrate

# Local development
cd API
python manage.py makemigrations
python manage.py migrate
```

## 🗄️ Data Migration (If You Have Existing Data)

### **Option 1: Fresh Start (Recommended)**

```bash
# Start fresh with PostgreSQL
docker-compose down -v  # Remove all volumes
docker-compose up --build
# Recreate your test data using the test data scripts
```

### **Option 2: Export/Import Data**

```bash
# Export from SQLite
cd API
python manage.py dumpdata --natural-foreign --natural-primary > data.json

# Start PostgreSQL container
docker-compose up postgres -d

# Import to PostgreSQL (after Django connects to PostgreSQL)
python manage.py loaddata data.json
```

## 🐳 Docker Container Details

### **PostgreSQL Container**

- **Image**: `postgres:15-alpine`
- **Port**: `5432`
- **Volume**: `postgres_data` (persistent storage)
- **Health Check**: Ensures PostgreSQL is ready before Django starts

### **Django Container**

- **Dependencies**: Waits for PostgreSQL to be healthy
- **Environment**: All database connection variables
- **Migrations**: Automatically runs on startup

## 🔍 Troubleshooting

### **PostgreSQL Connection Issues**

```bash
# Check if PostgreSQL is running
docker-compose ps

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection manually
docker-compose exec postgres psql -U postgres -d moneymanagement
```

### **Migration Issues**

```bash
# Reset migrations (WARNING: This will delete all data)
docker-compose down -v
docker-compose up --build

# Check Django logs
docker-compose logs money-management-api
```

### **Permission Issues**

```bash
# Fix volume permissions
docker-compose down
docker volume rm homemoneymanagement_postgres_data
docker-compose up --build
```

## 📈 Performance Benefits

### **PostgreSQL Advantages**

- ✅ **Better concurrency** - Multiple users can access simultaneously
- ✅ **ACID compliance** - Better data integrity
- ✅ **Advanced features** - JSON fields, full-text search, etc.
- ✅ **Scalability** - Can handle much larger datasets
- ✅ **Backup/Recovery** - Professional database features

### **Container Benefits**

- ✅ **Consistent environment** - Same setup everywhere
- ✅ **Easy deployment** - One command to start everything
- ✅ **Isolation** - Database doesn't interfere with host system
- ✅ **Portability** - Works on any system with Docker

## 🔒 Security Considerations

### **Production Setup**

For production, update these settings:

```yaml
# docker-compose.prod.yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Use strong password
    ports: []  # Don't expose port in production
```

### **Production Environment Variables**

```bash
# .env file for production
POSTGRES_PASSWORD=your_strong_password_here
POSTGRES_USER=your_custom_user
POSTGRES_DB=your_custom_db_name
```

## 📝 Next Steps

1. **Test the migration** - Verify all functionality works
2. **Update documentation** - Update any deployment docs
3. **Consider Redis** - Add caching for better performance
4. **Backup strategy** - Set up regular PostgreSQL backups
5. **Monitoring** - Add database monitoring and logging

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Verify environment variables are set correctly
3. Ensure PostgreSQL container is healthy before Django starts
4. Check that all migrations have been applied

The migration maintains full backward compatibility - your existing code will work exactly the same, just with a more robust database backend!

## 📁 File Handling

### **File Storage Architecture**

- **Database (PostgreSQL)**: Stores file metadata (filename, size, upload date, etc.)
- **Filesystem**: Stores actual PDF files in persistent Docker volume
- **Volume**: `media_files` volume ensures uploaded files survive container restarts

### **File Migration (If You Have Existing Files)**

```bash
# If you have existing uploaded files in API/media/
# Copy them to the new volume location
docker-compose up -d
docker cp API/media/. money-management-api:/HomeMoneyManagement/media/
```

### **File Access**

- **Local Development**: Files accessible at `API/media/`
- **Docker Environment**: Files stored in persistent volume
- **URL Access**: Files served at `http://localhost:8000/media/`

### **File Upload Features**

Your app supports:

- ✅ **PDF Bank Statement Uploads** - Up to 10MB
- ✅ **File Validation** - Checks PDF headers and extensions
- ✅ **Organized Storage** - Files stored by user/date structure
- ✅ **Metadata Tracking** - File size, upload date, processing status
- ✅ **Persistent Storage** - Files survive container restarts
