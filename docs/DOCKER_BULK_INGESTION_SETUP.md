# Docker Bulk Ingestion Setup Guide

## Problem: Windows Path Access in Docker

When running SAM in Docker, the container runs in a Linux environment and cannot directly access Windows file paths like `C:\Users\vin\Downloads\PDF`. This guide shows you how to fix this.

## Solution 1: Update Docker Compose (Recommended)

### Step 1: Stop SAM Docker
```bash
docker-compose down
```

### Step 2: Edit docker-compose.yml
Add volume mounts to give the container access to your Windows directories:

```yaml
services:
  sam-app:
    volumes:
      # ... existing volumes ...
      # Host file system access for bulk ingestion
      - C:\Users:/app/host_users:ro
      # Alternative: Mount specific directories
      - C:\Users\vin\Downloads:/app/host_downloads:ro
      - C:\Users\vin\Documents:/app/host_documents:ro
```

### Step 3: Restart SAM Docker
```bash
docker-compose up -d
```

### Step 4: Use Mapped Paths in SAM
Instead of using `C:\Users\vin\Downloads\PDF`, use:
- `/app/host_users/vin/Downloads/PDF` (if using full Users mount)
- `/app/host_downloads/PDF` (if using specific Downloads mount)

## Solution 2: Copy Files to Docker Volume

### Step 1: Copy files to SAM's upload directory
```bash
# Create a directory in SAM's uploads volume
docker exec sam-main mkdir -p /app/uploads/bulk_docs

# Copy files from Windows to container
docker cp "C:\Users\vin\Downloads\PDF" sam-main:/app/uploads/bulk_docs/
```

### Step 2: Use Container Path in SAM
Use the path: `/app/uploads/bulk_docs/PDF`

## Solution 3: Use Docker Desktop File Sharing

### Step 1: Open Docker Desktop Settings
- Go to Settings → Resources → File Sharing
- Add `C:\Users` to the shared directories
- Apply & Restart

### Step 2: Update docker-compose.yml
```yaml
volumes:
  - C:\Users:/app/host_users:ro
```

## Path Mapping Reference

| Windows Path | Docker Container Path | Mount Required |
|-------------|----------------------|----------------|
| `C:\Users\vin\Downloads` | `/app/host_users/vin/Downloads` | `C:\Users:/app/host_users:ro` |
| `C:\Users\vin\Documents` | `/app/host_users/vin/Documents` | `C:\Users:/app/host_users:ro` |
| `D:\MyFiles` | `/app/host_d/MyFiles` | `D:\:/app/host_d:ro` |

## Troubleshooting

### Error: "Path does not exist"
1. Check if the volume mount is correctly added to docker-compose.yml
2. Restart Docker containers after changing docker-compose.yml
3. Verify the Windows path exists and is accessible

### Error: "Permission denied"
1. Add `:ro` (read-only) to volume mounts for security
2. Ensure Docker Desktop has permission to access the directory
3. Check Windows folder permissions

### Error: "Directory is not readable"
1. Make sure the directory isn't empty
2. Check if antivirus software is blocking access
3. Try mounting a parent directory instead

## Security Notes

- Always use `:ro` (read-only) mounts for security
- Only mount directories you need for ingestion
- Avoid mounting system directories like `C:\Windows`

## Example Complete docker-compose.yml

```yaml
version: '3.8'

services:
  sam-app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: sam-main
    volumes:
      # SAM data volumes
      - sam_data:/app/data
      - sam_memory:/app/memory_store
      - sam_logs:/app/logs
      
      # Host file system access (Windows)
      - C:\Users:/app/host_users:ro
      - D:\Documents:/app/host_documents:ro
      
    ports:
      - "8502:8502"
      - "8501:8501"
    # ... rest of configuration
```

## Testing the Setup

1. After updating docker-compose.yml and restarting:
2. Go to SAM's Bulk Ingestion page
3. Try path: `/app/host_users/vin/Downloads/PDF`
4. You should see: ✅ Path validation successful

## Need Help?

If you're still having issues:
1. Check the Docker logs: `docker logs sam-main`
2. Verify your Windows path exists: `dir "C:\Users\vin\Downloads\PDF"`
3. Test the mount: `docker exec sam-main ls -la /app/host_users/vin/Downloads/`
