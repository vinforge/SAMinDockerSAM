## 🚀 Quick Start

### Windows (PowerShell)
```powershell
# Download the release
Invoke-WebRequest -Uri "https://github.com/forge-1825/SAM/releases/download/v1.0.0-docker/sam-docker-v1.0.0-docker.tar.gz" -OutFile "sam-docker-v1.0.0-docker.tar.gz"

# Extract and start
tar -xzf sam-docker-v1.0.0-docker.tar.gz
cd sam-docker-v1.0.0-docker
.\quick_start.bat

Linux/macOS (Terminal)

# Download the release
wget https://github.com/forge-1825/SAM/releases/download/v1.0.0-docker/sam-docker-v1.0.0-docker.tar.gz

# Extract and start
tar -xzf sam-docker-v1.0.0-docker.tar.gz
cd sam-docker-v1.0.0-docker
./quick_start.sh

Access SAM at: http://localhost:8502

📦 What's Included
Complete SAM Stack: AI assistant with memory capabilities
Cross-platform scripts: Windows batch file + Linux/macOS shell script
Comprehensive documentation: Windows-specific guide included
Management tools: Complete Docker management script
Production-ready: Health checks, monitoring, persistence
📋 System Requirements
Docker Desktop (Windows/macOS) or Docker Engine (Linux)
4GB RAM minimum (8GB+ recommended)
10GB+ free disk space
🛠️ Management
Use the included management script:

./manage_sam.sh start          # Start services
./manage_sam.sh stop           # Stop services
./manage_sam.sh status         # Check status
./manage_sam.sh logs           # View logs
./manage_sam.sh backup         # Create backup

📚 Documentation
Windows Guide: WINDOWS_INSTALLATION_GUIDE.md
Complete Guide: DOCKER_DEPLOYMENT_GUIDE.md
Docker README: README_DOCKER.md
🌟 Benefits
5-minute deployment vs 30-minute traditional setup
Complete environment isolation
Production-ready out of the box
Cross-platform support (Windows, Linux, macOS)
No dependency management required



### **Step 3: Upload the Release File**

1. **Drag and drop** or **click "Attach binaries"** 
2. Upload the file: `sam-docker-v1.0.0-docker.tar.gz` 
   - This should be in your `release/` folder from our earlier work

### **Step 4: Publish**

1. **Uncheck "Set as a pre-release"** (if checked)
2. **Check "Set as the latest release"** (if available)
3. Click **"Publish release"**

### **Step 5: Test the Download**

Once published, your PowerShell command should work:

```powershell
Invoke-WebRequest -Uri "https://github.com/forge-1825/SAM/releases/download/v1.0.0-docker/sam-docker-v1.0.0-docker.tar.gz" -OutFile "sam-docker-v1.0.0-docker.tar.gz"
