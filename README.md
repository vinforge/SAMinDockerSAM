# 🐳 SAM Docker - Containerized AI Assistant

**SAM (Secure AI Memory)** - Advanced AI assistant with human-like conceptual understanding, packaged as a Docker container for easy deployment.

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** (Windows/macOS) or **Docker Engine** (Linux)
- **4GB RAM** minimum (8GB+ recommended)
- **10GB+ free disk space**

### One-Command Deployment

#### **Windows (PowerShell)**
```powershell
# Clone the repository
git clone https://github.com/vinforge/SAMinDockerSAM.git
cd SAMinDockerSAM

# Start SAM
.\docker\quick_start.bat
```

#### **Linux/macOS (Terminal)**
```bash
# Clone the repository
git clone https://github.com/vinforge/SAMinDockerSAM.git
cd SAMinDockerSAM

# Start SAM
./docker/quick_start.sh
```

**Access SAM at: http://localhost:8502**

## ✨ **Latest Updates for Chat Users**

- **📁 Enhanced Document Processing**: Drag & drop file upload directly in chat
- **💬 Improved Conversation Isolation**: True 'New Chat' functionality
- **🧠 Better Memory Management**: Enhanced search and organization
- **🔒 Streamlined Security**: Simplified setup with robust encryption
- **🎯 Optimized for Daily Use**: Focus on smooth chat experience

## 📦 What's Included

- **🧠 Complete SAM AI Assistant**: Advanced AI with memory capabilities
- **🐳 Docker Container Stack**: SAM + Redis + ChromaDB
- **🪟 Cross-Platform Support**: Windows, Linux, macOS
- **📚 Comprehensive Documentation**: Complete setup and usage guides
- **🛠️ Management Tools**: Easy container management scripts

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SAM Main App  │    │     Redis       │    │    ChromaDB     │
│   (Streamlit)   │◄──►│    (Cache)      │    │   (Vectors)     │
│   Port: 8502    │    │   Port: 6379    │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Services**:
- **SAM Main App**: Core AI assistant (Port 8502)
- **Memory Control Center**: Advanced memory management (Port 8501)
- **Setup Interface**: First-time configuration (Port 8503)
- **Redis**: Session and cache management
- **ChromaDB**: Vector database for embeddings

## 🛠️ Management

### Quick Commands
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Advanced Management
```bash
# Use the management script
./docker/manage_sam.sh start          # Start services
./docker/manage_sam.sh stop           # Stop services
./docker/manage_sam.sh status         # Check status
./docker/manage_sam.sh logs           # View logs
./docker/manage_sam.sh backup         # Create backup
./docker/manage_sam.sh update         # Update SAM
```

## 💾 Data Persistence

All data is preserved in Docker volumes:
- **Application data**: Documents and knowledge base
- **Memory store**: Conversation history and learned concepts
- **Security configs**: Encryption keys and authentication
- **Logs and cache**: Performance and diagnostic data

## 📚 Documentation

- **[Docker Deployment Guide](DOCKER_DEPLOYMENT_GUIDE.md)**: Complete deployment documentation
- **[Windows Installation Guide](WINDOWS_INSTALLATION_GUIDE.md)**: Windows-specific instructions
- **[Management Scripts](docker/)**: Container management tools

## 🔒 Security Features

- **Encrypted data storage** with secure key management
- **Isolated container environment** with controlled access
- **Non-root container execution** for enhanced security
- **Secure session management** with Redis

## 📋 System Requirements

### Minimum
- **OS**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **RAM**: 4GB
- **Storage**: 10GB free space
- **CPU**: 2 cores

### Recommended
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **CPU**: 4+ cores
- **Network**: Stable internet connection

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/vinforge/SAMinDockerSAM/issues)
- **Documentation**: Complete guides included
- **Original Project**: [SAM Main Repository](https://github.com/forge-1825/SAM)

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

**🎉 Experience the future of AI assistance with SAM Docker!** 🚀

*Containerized for your convenience, powered by advanced AI technology.*
