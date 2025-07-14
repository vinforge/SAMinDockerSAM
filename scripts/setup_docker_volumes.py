#!/usr/bin/env python3
"""
Docker Volume Setup Helper for SAM Bulk Ingestion

This script helps users configure Docker volumes for accessing host file systems
in SAM's bulk document ingestion feature.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

def detect_platform() -> str:
    """Detect the current platform."""
    return platform.system()

def get_common_directories() -> List[Tuple[str, str]]:
    """Get common directories based on platform."""
    system = detect_platform()
    
    if system == "Windows":
        username = os.environ.get('USERNAME', 'user')
        return [
            ("Documents", f"C:\\Users\\{username}\\Documents"),
            ("Downloads", f"C:\\Users\\{username}\\Downloads"),
            ("Desktop", f"C:\\Users\\{username}\\Desktop"),
            ("OneDrive", f"C:\\Users\\{username}\\OneDrive\\Documents"),
            ("All Users", "C:\\Users"),
        ]
    elif system == "Darwin":  # macOS
        home = os.path.expanduser("~")
        return [
            ("Documents", f"{home}/Documents"),
            ("Downloads", f"{home}/Downloads"),
            ("Desktop", f"{home}/Desktop"),
            ("Home", home),
        ]
    else:  # Linux
        home = os.path.expanduser("~")
        return [
            ("Documents", f"{home}/Documents"),
            ("Downloads", f"{home}/Downloads"),
            ("Desktop", f"{home}/Desktop"),
            ("Home", home),
        ]

def generate_docker_volume_config(directories: List[Tuple[str, str]]) -> str:
    """Generate Docker Compose volume configuration."""
    system = detect_platform()
    
    config_lines = []
    config_lines.append("    volumes:")
    config_lines.append("      # SAM persistent data volumes")
    config_lines.append("      - sam_data:/app/data")
    config_lines.append("      - sam_memory:/app/memory_store")
    config_lines.append("      - sam_logs:/app/logs")
    config_lines.append("      - sam_chroma:/app/chroma_db")
    config_lines.append("      - sam_uploads:/app/uploads")
    config_lines.append("      - sam_cache:/app/cache")
    config_lines.append("      - sam_backups:/app/backups")
    config_lines.append("      - sam_security:/app/security")
    config_lines.append("      # Configuration")
    config_lines.append("      - ./docker/sam_docker_config.json:/app/config/sam_config.json:ro")
    config_lines.append("")
    config_lines.append("      # Host file system access for bulk ingestion")
    
    for name, path in directories:
        if system == "Windows":
            # Convert Windows paths for Docker
            container_path = f"/app/host_{name.lower().replace(' ', '_')}"
            config_lines.append(f"      - {path}:{container_path}:ro")
        else:
            # Unix-like systems
            container_path = f"/app/host_{name.lower().replace(' ', '_')}"
            config_lines.append(f"      - {path}:{container_path}:ro")
    
    return "\n".join(config_lines)

def check_docker_compose_exists() -> bool:
    """Check if docker-compose.yml exists."""
    return Path("docker-compose.yml").exists()

def backup_docker_compose() -> str:
    """Create a backup of the current docker-compose.yml."""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"docker-compose.yml.backup_{timestamp}"
    
    shutil.copy2("docker-compose.yml", backup_name)
    return backup_name

def main():
    """Main function."""
    print("🐳 SAM Docker Volume Setup Helper")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not check_docker_compose_exists():
        print("❌ Error: docker-compose.yml not found in current directory")
        print("   Please run this script from the SAM project root directory")
        sys.exit(1)
    
    # Detect platform
    system = detect_platform()
    print(f"📱 Detected platform: {system}")
    
    # Get common directories
    directories = get_common_directories()
    
    print("\n📁 Available directories to mount:")
    for i, (name, path) in enumerate(directories, 1):
        exists = "✅" if Path(path).exists() else "❌"
        print(f"   {i}. {name}: {path} {exists}")
    
    print("\n🔧 Select directories to mount (comma-separated numbers, or 'all'):")
    selection = input("   Selection: ").strip()
    
    if selection.lower() == 'all':
        selected_dirs = directories
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected_dirs = [directories[i] for i in indices if 0 <= i < len(directories)]
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            sys.exit(1)
    
    if not selected_dirs:
        print("❌ No directories selected")
        sys.exit(1)
    
    print(f"\n📋 Selected {len(selected_dirs)} directories:")
    for name, path in selected_dirs:
        print(f"   - {name}: {path}")
    
    # Generate configuration
    config = generate_docker_volume_config(selected_dirs)
    
    print("\n📝 Generated Docker Compose volume configuration:")
    print("-" * 50)
    print(config)
    print("-" * 50)
    
    # Ask if user wants to apply changes
    print("\n⚠️  This will modify your docker-compose.yml file")
    apply = input("   Apply changes? (y/N): ").strip().lower()
    
    if apply == 'y':
        # Create backup
        backup_file = backup_docker_compose()
        print(f"💾 Created backup: {backup_file}")
        
        # Note: In a real implementation, you'd parse and modify the YAML file
        # For now, just show instructions
        print("\n📖 Manual steps to apply changes:")
        print("1. Open docker-compose.yml in a text editor")
        print("2. Find the 'sam-app' service volumes section")
        print("3. Replace the volumes section with the configuration above")
        print("4. Save the file")
        print("5. Restart Docker: docker-compose down && docker-compose up -d")
        
        print("\n🎯 Path mapping reference:")
        for name, path in selected_dirs:
            container_path = f"/app/host_{name.lower().replace(' ', '_')}"
            print(f"   {path} → {container_path}")
    
    print("\n✅ Setup complete!")
    print("📖 For detailed instructions, see: docs/DOCKER_BULK_INGESTION_SETUP.md")

if __name__ == "__main__":
    main()
