"""
SAM Bulk Ingestion UI - Phase 2
Streamlit interface for managing bulk document ingestion sources and operations.
"""

import streamlit as st
import json
import subprocess
import threading
import time
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

class BulkIngestionManager:
    """Manages bulk ingestion sources and operations."""
    
    def __init__(self):
        self.config_file = Path("data/bulk_ingestion_config.json")
        self.state_db = Path("data/ingestion_state.db")
        self.log_file = Path("logs/bulk_ingest.log")
        
        # Ensure directories exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize configuration
        self._init_config()
    
    def _init_config(self):
        """Initialize configuration file if it doesn't exist."""
        if not self.config_file.exists():
            default_config = {
                "version": "1.0",
                "sources": [],
                "settings": {
                    "auto_scan_enabled": False,
                    "scan_interval_minutes": 60,
                    "default_file_types": ["pdf", "txt", "md", "docx", "py", "js", "json"],
                    "max_file_size_mb": 100,
                    "enable_notifications": True
                },
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading configuration: {e}")
            return {"sources": [], "settings": {}}
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            config["last_updated"] = datetime.now().isoformat()
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            st.error(f"Error saving configuration: {e}")
    
    def add_source(self, path: str, name: str, file_types: List[str], enabled: bool = True) -> bool:
        """Add a new ingestion source."""
        try:
            config = self.load_config()
            
            # Check if source already exists
            for source in config["sources"]:
                if source["path"] == path:
                    return False
            
            new_source = {
                "id": f"source_{len(config['sources']) + 1}",
                "name": name,
                "path": path,
                "file_types": file_types,
                "enabled": enabled,
                "added_date": datetime.now().isoformat(),
                "last_scanned": None,
                "status": "ready",
                "files_processed": 0,
                "last_scan_results": {}
            }
            
            config["sources"].append(new_source)
            self.save_config(config)
            return True
            
        except Exception as e:
            st.error(f"Error adding source: {e}")
            return False
    
    def remove_source(self, source_id: str) -> bool:
        """Remove an ingestion source."""
        try:
            config = self.load_config()
            config["sources"] = [s for s in config["sources"] if s["id"] != source_id]
            self.save_config(config)
            return True
        except Exception as e:
            st.error(f"Error removing source: {e}")
            return False
    
    def update_source(self, source_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing source."""
        try:
            config = self.load_config()
            for source in config["sources"]:
                if source["id"] == source_id:
                    source.update(updates)
                    break
            self.save_config(config)
            return True
        except Exception as e:
            st.error(f"Error updating source: {e}")
            return False
    
    def get_ingestion_stats(self, page: int = 1, page_size: int = 30) -> Dict[str, Any]:
        """Get ingestion statistics from the state database with pagination."""
        try:
            if not self.state_db.exists():
                return {
                    'total_files': 0,
                    'total_chunks': 0,
                    'avg_enrichment': 0.0,
                    'successful': 0,
                    'failed': 0,
                    'recent_activity': [],
                    'total_pages': 0,
                    'current_page': 1,
                    'has_next': False,
                    'has_prev': False
                }

            with sqlite3.connect(self.state_db) as conn:
                # Get summary statistics
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_files,
                        SUM(chunks_created) as total_chunks,
                        AVG(enrichment_score) as avg_enrichment,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
                    FROM processed_files
                """)
                result = cursor.fetchone()

                total_files = result[0] or 0
                total_pages = (total_files + page_size - 1) // page_size if total_files > 0 else 1

                # Calculate offset for pagination
                offset = (page - 1) * page_size

                # Get paginated activity
                activity_cursor = conn.execute("""
                    SELECT filepath, processed_at, status, enrichment_score, chunks_created, file_size
                    FROM processed_files
                    ORDER BY processed_at DESC
                    LIMIT ? OFFSET ?
                """, (page_size, offset))
                activity_results = activity_cursor.fetchall()

                return {
                    'total_files': total_files,
                    'total_chunks': result[1] or 0,
                    'avg_enrichment': result[2] or 0.0,
                    'successful': result[3] or 0,
                    'failed': result[4] or 0,
                    'recent_activity': [
                        {
                            'filepath': row[0],
                            'processed_at': row[1],
                            'status': row[2],
                            'enrichment_score': row[3],
                            'chunks_created': row[4],
                            'file_size': row[5] if len(row) > 5 else 0
                        }
                        for row in activity_results
                    ],
                    'total_pages': total_pages,
                    'current_page': page,
                    'has_next': page < total_pages,
                    'has_prev': page > 1,
                    'page_size': page_size
                }
        except Exception as e:
            st.error(f"Error getting stats: {e}")
            return {
                'total_files': 0,
                'total_chunks': 0,
                'avg_enrichment': 0.0,
                'successful': 0,
                'failed': 0,
                'recent_activity': [],
                'total_pages': 0,
                'current_page': 1,
                'has_next': False,
                'has_prev': False
            }
    
    def get_source_preview(self, source_path: str, file_types: List[str]) -> Dict[str, Any]:
        """Get preview of what files would be processed vs skipped."""
        try:
            # Build command for dry run preview
            cmd = [
                sys.executable, "scripts/bulk_ingest.py",
                "--source", source_path,
                "--dry-run",
                "--verbose"
            ]

            if file_types:
                cmd.extend(["--file-types", ",".join(file_types)])

            # Run command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )

            # Parse output to extract file counts
            stdout = result.stdout
            processed_count = 0
            skipped_count = 0
            failed_count = 0
            total_found = 0

            if "Bulk Ingestion Summary:" in stdout:
                lines = stdout.split('\n')
                for line in lines:
                    if "Processed:" in line:
                        processed_count = int(line.split(':')[1].strip())
                    elif "Skipped:" in line:
                        skipped_count = int(line.split(':')[1].strip())
                    elif "Failed:" in line:
                        failed_count = int(line.split(':')[1].strip())
                    elif "Total found:" in line:
                        total_found = int(line.split(':')[1].strip())

            return {
                "success": result.returncode == 0,
                "new_files": processed_count,
                "already_processed": skipped_count,
                "failed": failed_count,
                "total_found": total_found,
                "stdout": stdout,
                "stderr": result.stderr,
                "incremental_info": {
                    "will_process": processed_count,
                    "already_ingested": skipped_count,
                    "total_discovered": total_found,
                    "efficiency_ratio": f"{skipped_count}/{total_found}" if total_found > 0 else "0/0"
                }
            }

        except Exception as e:
            return {
                "success": False,
                "new_files": 0,
                "already_processed": 0,
                "failed": 0,
                "total_found": 0,
                "stdout": "",
                "stderr": str(e),
                "incremental_info": {
                    "will_process": 0,
                    "already_ingested": 0,
                    "total_discovered": 0,
                    "efficiency_ratio": "0/0"
                }
            }

    def run_bulk_ingestion(self, source_path: str, file_types: List[str], dry_run: bool = False) -> Dict[str, Any]:
        """Run bulk ingestion for a specific source."""
        try:
            # Build command
            cmd = [
                sys.executable, "scripts/bulk_ingest.py",
                "--source", source_path
            ]
            
            if file_types:
                cmd.extend(["--file-types", ",".join(file_types)])
            
            if dry_run:
                cmd.append("--dry-run")
            
            cmd.append("--verbose")
            
            # Run command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1
            }

class BulkIngestionUI:
    """Streamlit UI for bulk ingestion management."""
    
    def __init__(self):
        self.manager = BulkIngestionManager()
    
    def render(self):
        """Render the bulk ingestion UI."""
        st.subheader("📁 Bulk Document Ingestion")
        st.markdown("Manage document sources and bulk ingestion operations")
        
        # Create tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📂 Source Management",
            "🚀 Manual Scan",
            "📊 Statistics",
            "⚙️ Settings",
            "🔬 Discovery Cycle"
        ])
        
        with tab1:
            self._render_source_management()
        
        with tab2:
            self._render_manual_scan()
        
        with tab3:
            self._render_statistics()
        
        with tab4:
            self._render_settings()

        with tab5:
            self._render_discovery_cycle()
    
    def _render_source_management(self):
        """Render the source management interface."""
        st.markdown("### 📂 Manage Knowledge Sources")
        st.markdown("Add and manage folders that SAM monitors for documents")

        # Information panel
        with st.expander("ℹ️ How Document Processing Works", expanded=False):
            st.markdown("""
            **What happens when you add and process sources:**

            1. **📁 Add Source:** Configure a folder path and file types to monitor
            2. **🚀 Process Files:** Scan the folder and process supported documents
            3. **🧠 Data Enrichment:** Extract content, generate embeddings, and create metadata
            4. **💾 Memory Storage:** Store processed content in SAM's knowledge base
            5. **🔍 Knowledge Consolidation:** Optimize and organize memories for better retrieval
            6. **💬 Ready for Q&A:** Ask SAM questions about the processed documents

            **Processing Options:**
            - **🔍 Preview (Dry Run):** See what files will be processed without actually processing them
            - **🚀 Process:** Actually process files and add them to SAM's knowledge base
            - **🧠 Auto-Consolidate:** Automatically run knowledge consolidation after processing

            **Note:** Adding a source only configures it - you must trigger processing to add files to SAM's knowledge base.
            """)

        st.divider()
        
        config = self.manager.load_config()
        sources = config.get("sources", [])
        
        # Add new source section
        with st.expander("➕ Add New Source", expanded=len(sources) == 0):
            # Use a form to ensure proper handling of inputs and button
            with st.form("add_source_form", clear_on_submit=True):
                col1, col2 = st.columns([2, 1])

                with col1:
                    # Enhanced path input with platform-specific examples and folder browser
                    import platform
                    import os
                    from pathlib import Path

                    system = platform.system()

                    if system == "Windows":
                        placeholder = "C:\\Users\\username\\Documents"
                        help_text = "Enter the full Windows path (e.g., C:\\Users\\username\\Documents)"
                    elif system == "Darwin":  # macOS
                        placeholder = "/Users/username/Documents"
                        help_text = "Enter the full macOS path (e.g., /Users/username/Documents or ~/Documents)"
                    else:  # Linux and others
                        placeholder = "/home/username/documents"
                        help_text = "Enter the full Linux path (e.g., /home/username/documents or ~/documents)"

                    # Folder path input with browser functionality
                    st.markdown("**📁 Select Folder to Ingest:**")

                    # Initialize session state for folder browser with robust path handling
                    if 'current_browse_path' not in st.session_state:
                        try:
                            # Use user's home directory as default
                            home_path = Path.home()
                            if home_path.exists() and home_path.is_dir():
                                st.session_state.current_browse_path = str(home_path)
                            else:
                                # Fallback to current working directory
                                st.session_state.current_browse_path = str(Path.cwd())
                        except Exception as e:
                            # Ultimate fallback to root or current directory
                            st.session_state.current_browse_path = str(Path.cwd())
                            st.warning(f"⚠️ Could not access home directory: {e}")

                    if 'selected_folder_path' not in st.session_state:
                        st.session_state.selected_folder_path = ""

                    # Validate current browse path and reset if invalid
                    try:
                        current_path_obj = Path(st.session_state.current_browse_path)
                        if not current_path_obj.exists() or not current_path_obj.is_dir():
                            st.warning(f"⚠️ Invalid path detected: {st.session_state.current_browse_path}")
                            st.session_state.current_browse_path = str(Path.home())
                            st.info("🔄 Reset to home directory")
                    except Exception as e:
                        st.error(f"❌ Path validation error: {e}")
                        st.session_state.current_browse_path = str(Path.cwd())
                        st.info("🔄 Reset to current directory")

                    # Folder browser toggle
                    use_browser = st.checkbox("🗂️ Use Folder Browser", key="use_folder_browser",
                                            help="Browse and select folders visually instead of typing paths")

                    if use_browser:
                        # Folder browser interface
                        st.markdown("**Current Location:**")
                        current_path = Path(st.session_state.current_browse_path)
                        st.code(str(current_path))

                        # Navigation buttons (moved outside form)
                        st.markdown("**📁 Navigate Folders:**")
                        col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 1, 1, 2])

                        with col_nav1:
                            nav_parent = st.form_submit_button("⬆️ Parent")
                            if nav_parent:
                                parent = current_path.parent
                                if parent != current_path:  # Not at root
                                    st.session_state.current_browse_path = str(parent)
                                    st.rerun()

                        with col_nav2:
                            nav_home = st.form_submit_button("🏠 Home")
                            if nav_home:
                                try:
                                    home_path = Path.home()
                                    if home_path.exists():
                                        st.session_state.current_browse_path = str(home_path)
                                    else:
                                        st.session_state.current_browse_path = str(Path.cwd())
                                        st.warning("⚠️ Home directory not accessible, using current directory")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error navigating to home: {e}")
                                    st.session_state.current_browse_path = str(Path.cwd())
                                    st.rerun()

                        with col_nav3:
                            reset_browser = st.form_submit_button("🔄 Reset")
                            if reset_browser:
                                try:
                                    # Clear session state and reset to safe default
                                    st.session_state.current_browse_path = str(Path.home())
                                    st.session_state.selected_folder_path = ""
                                    st.success("🔄 Browser reset to home directory")
                                    st.rerun()
                                except Exception as e:
                                    st.session_state.current_browse_path = str(Path.cwd())
                                    st.session_state.selected_folder_path = ""
                                    st.warning(f"⚠️ Reset to current directory: {e}")
                                    st.rerun()

                        with col_nav4:
                            # Quick navigation to common folders
                            common_folders = []
                            if system == "Windows":
                                common_folders = [
                                    ("📄 Documents", str(Path.home() / "Documents")),
                                    ("📥 Downloads", str(Path.home() / "Downloads")),
                                    ("🖥️ Desktop", str(Path.home() / "Desktop")),
                                ]
                            else:
                                common_folders = [
                                    ("📄 Documents", str(Path.home() / "Documents")),
                                    ("📥 Downloads", str(Path.home() / "Downloads")),
                                    ("🖥️ Desktop", str(Path.home() / "Desktop")),
                                ]

                            selected_common = st.selectbox(
                                "Quick Navigation",
                                options=[""] + [f[0] for f in common_folders],
                                key="quick_nav"
                            )

                            if selected_common:
                                for name, path in common_folders:
                                    if name == selected_common and Path(path).exists():
                                        st.session_state.current_browse_path = path
                                        st.rerun()

                        # List directories in current path with enhanced error handling
                        try:
                            # Validate current path before listing
                            if not current_path.exists():
                                st.error(f"❌ Path does not exist: {current_path}")
                                st.info("🔄 Resetting to home directory...")
                                st.session_state.current_browse_path = str(Path.home())
                                st.rerun()
                                return

                            if not current_path.is_dir():
                                st.error(f"❌ Path is not a directory: {current_path}")
                                st.info("🔄 Resetting to home directory...")
                                st.session_state.current_browse_path = str(Path.home())
                                st.rerun()
                                return

                            directories = []
                            try:
                                for item in current_path.iterdir():
                                    if item.is_dir() and not item.name.startswith('.'):
                                        directories.append(item)
                            except PermissionError:
                                st.error("❌ Permission denied - cannot access this folder")
                                return
                            except Exception as iter_error:
                                st.error(f"❌ Error reading directory contents: {iter_error}")
                                return

                            directories.sort(key=lambda x: x.name.lower())

                            if directories:
                                st.markdown("**📁 Available Folders:**")

                                # Display folders as a selectbox instead of buttons (form-compatible)
                                folder_options = ["Select a folder..."] + [f"📁 {folder.name}" for folder in directories]
                                selected_folder_idx = st.selectbox(
                                    "Choose a folder to navigate to:",
                                    range(len(folder_options)),
                                    format_func=lambda x: folder_options[x],
                                    key="folder_selector"
                                )

                                if selected_folder_idx > 0:
                                    selected_folder = directories[selected_folder_idx - 1]
                                    navigate_to_folder = st.form_submit_button(f"📁 Navigate to {selected_folder.name}")
                                    if navigate_to_folder:
                                        st.session_state.current_browse_path = str(selected_folder)
                                        st.rerun()

                                # Select current folder button
                                st.markdown("---")
                                col_select1, col_select2 = st.columns([1, 1])

                                with col_select1:
                                    select_current = st.form_submit_button("✅ Select This Folder", type="primary")
                                    if select_current:
                                        st.session_state.selected_folder_path = str(current_path)
                                        st.success(f"Selected: {current_path}")

                                with col_select2:
                                    if st.session_state.selected_folder_path:
                                        st.info(f"Selected: {Path(st.session_state.selected_folder_path).name}")
                            else:
                                st.info("No subdirectories found in this location")

                                # Still allow selecting the current folder
                                select_empty = st.form_submit_button("✅ Select This Folder", type="primary")
                                if select_empty:
                                    st.session_state.selected_folder_path = str(current_path)
                                    st.success(f"Selected: {current_path}")

                        except PermissionError:
                            st.error("❌ Permission denied - cannot access this folder")
                        except Exception as e:
                            st.error(f"❌ Error browsing folder: {e}")

                        # Use selected path
                        source_path = st.session_state.selected_folder_path

                        # Show selected path
                        if source_path:
                            st.markdown("**Selected Folder:**")
                            st.code(source_path)
                    else:
                        # Manual path input
                        source_path = st.text_input(
                            "Folder Path",
                            placeholder=placeholder,
                            help=help_text,
                            key="new_source_path"
                        )

                    source_name = st.text_input(
                        "Source Name",
                        placeholder="Research Papers",
                        help="A friendly name for this source",
                        key="new_source_name"
                    )
            
                with col2:
                    default_types = config.get("settings", {}).get("default_file_types", ["pdf", "txt", "md"])
                    file_types = st.multiselect(
                        "File Types",
                        options=["pdf", "txt", "md", "docx", "doc", "py", "js", "html", "json", "csv"],
                        default=default_types,
                        help="Select which file types to process",
                        key="new_source_file_types"
                    )

                    enabled = st.checkbox("Enable Source", value=True, key="new_source_enabled")

                # Processing options
                col1, col2 = st.columns(2)
                with col1:
                    auto_scan = st.checkbox(
                        "🚀 Scan immediately after adding",
                        value=True,
                        help="Automatically scan the source after adding it",
                        key="new_source_auto_scan"
                    )
                with col2:
                    dry_run_new = st.checkbox(
                        "🔍 Dry run first",
                        value=False,
                        help="Preview what will be processed before actual scanning",
                        key="new_source_dry_run"
                    )

                # Submit button for the form
                submitted = st.form_submit_button("➕ Add Source", type="primary")

            # Handle form submission outside the form
            if submitted:
                # Validate required fields
                if not source_path or not source_path.strip():
                    st.error("❌ Please enter a folder path")
                elif not source_name or not source_name.strip():
                    st.error("❌ Please enter a source name")
                elif not file_types:
                    st.error("❌ Please select at least one file type")
                else:
                    # Enhanced cross-platform path validation
                    path_validation = self._validate_path(source_path.strip())

                    if path_validation["valid"]:
                        # Use the normalized path
                        normalized_path = path_validation["normalized_path"]

                        # Check if source already exists
                        existing_sources = config.get("sources", [])
                        if any(s["path"] == normalized_path for s in existing_sources):
                            st.error(f"❌ Source with path '{normalized_path}' already exists")
                        elif any(s["name"] == source_name.strip() for s in existing_sources):
                            st.error(f"❌ Source with name '{source_name.strip()}' already exists")
                        else:
                            if self.manager.add_source(normalized_path, source_name.strip(), file_types, enabled):
                                st.success(f"✅ Successfully added source: {source_name.strip()}")
                                st.info(f"📁 Normalized path: `{normalized_path}`")
                                st.info(f"📄 File types: {', '.join(file_types)}")

                                # Auto-scan if requested
                                if auto_scan and enabled:
                                    st.info(f"🚀 {'Previewing' if dry_run_new else 'Processing'} files in {source_name.strip()}...")

                                    with st.spinner(f"{'Scanning' if dry_run_new else 'Processing'} {source_name.strip()}..."):
                                        result = self.manager.run_bulk_ingestion(
                                            normalized_path,
                                            file_types,
                                            dry_run=dry_run_new
                                        )

                                    # Display immediate results
                                    if result["success"]:
                                        st.success(f"✅ {source_name.strip()}: {'Preview' if dry_run_new else 'Processing'} completed!")

                                        # Show summary
                                        stdout = result["stdout"]
                                        if "Bulk Ingestion Summary:" in stdout:
                                            summary_start = stdout.find("Bulk Ingestion Summary:")
                                            summary_section = stdout[summary_start:summary_start+300]
                                            st.code(summary_section)

                                            if dry_run_new:
                                                st.info("🔍 This was a preview. Go to 'Manual Scan' tab to process files.")
                                            else:
                                                st.success("🎉 Files have been processed and added to SAM's knowledge base!")
                                    else:
                                        st.error(f"❌ {source_name.strip()}: {'Preview' if dry_run_new else 'Processing'} failed")
                                        if result["stderr"]:
                                            st.error(result["stderr"])

                                # Clear form fields by updating session state
                                if 'selected_folder_path' in st.session_state:
                                    st.session_state.selected_folder_path = ""

                                # Show success message and guidance
                                st.info("🔄 Source added successfully! Refresh the page or navigate to 'Manual Scan' tab to see the new source.")
                            else:
                                st.error("❌ Failed to add source. Please check the logs for details.")
                    else:
                        # Show detailed path validation error
                        st.error(f"❌ Path validation failed: {path_validation['error']}")

                        # Show debugging information using container instead of nested expander
                        st.markdown("**🔍 Path Debugging Information:**")
                        with st.container():
                            debug_info = f"""
Original path: {source_path}
Normalized path: {path_validation.get('normalized_path', 'N/A')}
Path exists: {path_validation.get('exists', False)}
Is directory: {path_validation.get('is_directory', False)}
Platform: {path_validation.get('platform', 'Unknown')}"""

                            # Add Docker mapping information if applicable
                            if path_validation.get('docker_mapped', False):
                                debug_info += f"""
Docker mapped: Yes
Mapped path: {path_validation.get('mapped_path', 'N/A')}"""

                            debug_info += f"""
Error details: {path_validation.get('error_details', 'None')}"""

                            st.code(debug_info)

                            # Show Docker-specific help if mapping was applied
                            if path_validation.get('docker_mapped', False):
                                st.warning("🐳 **Docker Path Mapping Detected**")
                                st.markdown("""
**To fix this issue:**
1. Update your `docker-compose.yml` to mount the Windows directory
2. Add this line under the `volumes:` section:
   ```yaml
   - C:\\Users:/app/host_users:ro
   ```
3. Restart Docker: `docker-compose down && docker-compose up -d`
4. Use the mapped path: `/app/host_users/vin/Downloads/PDF`

📖 **See the full guide:** `docs/DOCKER_BULK_INGESTION_SETUP.md`
                                """)

            # Add helpful path suggestions outside the form using container instead of nested expander
            st.markdown("**💡 Need help finding folder paths?**")
            with st.container():
                import platform
                system = platform.system()

                st.markdown("**Common Document Folder Paths:**")

                if system == "Windows":
                    common_paths = [
                        ("Documents", "C:\\Users\\%USERNAME%\\Documents"),
                        ("Desktop", "C:\\Users\\%USERNAME%\\Desktop"),
                        ("Downloads", "C:\\Users\\%USERNAME%\\Downloads"),
                        ("OneDrive", "C:\\Users\\%USERNAME%\\OneDrive\\Documents")
                    ]
                elif system == "Darwin":  # macOS
                    common_paths = [
                        ("Documents", "~/Documents"),
                        ("Desktop", "~/Desktop"),
                        ("Downloads", "~/Downloads"),
                        ("iCloud Drive", "~/Library/Mobile Documents/com~apple~CloudDocs")
                    ]
                else:  # Linux
                    common_paths = [
                        ("Documents", "~/Documents"),
                        ("Desktop", "~/Desktop"),
                        ("Downloads", "~/Downloads"),
                        ("Home", "~")
                    ]

                for name, path in common_paths:
                    st.code(f"{name}: {path}")

                st.markdown("**Tips:**")
                st.markdown("• Use the full path to the folder containing your documents")
                st.markdown("• Make sure the folder exists and you have read permissions")
                st.markdown("• On Windows, use backslashes (\\) or forward slashes (/)")
                st.markdown("• On macOS/Linux, use ~ for your home directory")

        # Display existing sources
        if sources:
            # Quick actions for all sources
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🚀 Process All Enabled Sources", type="secondary", key="process_all_sources_button"):
                    enabled_sources = [s for s in sources if s["enabled"]]
                    if enabled_sources:
                        st.session_state.trigger_bulk_scan = True
                        st.rerun()
                    else:
                        st.warning("⚠️ No enabled sources to process")

            with col2:
                if st.button("🔍 Preview All Sources", type="secondary", key="preview_all_sources_button_main"):
                    enabled_sources = [s for s in sources if s["enabled"]]
                    if enabled_sources:
                        st.session_state.trigger_bulk_preview = True
                        st.rerun()
                    else:
                        st.warning("⚠️ No enabled sources to preview")

            with col3:
                if st.button("📊 View Processing Stats", type="secondary", key="view_processing_stats_button"):
                    st.session_state.show_stats_popup = True

            # Handle bulk operations
            if st.session_state.get("trigger_bulk_scan", False):
                st.session_state.trigger_bulk_scan = False
                self._run_bulk_operation([s for s in sources if s["enabled"]], dry_run=False)

            if st.session_state.get("trigger_bulk_preview", False):
                st.session_state.trigger_bulk_preview = False
                self._run_bulk_operation([s for s in sources if s["enabled"]], dry_run=True)

            st.markdown("### 📋 Current Sources")

            for i, source in enumerate(sources):
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        status_icon = "🟢" if source["enabled"] else "🔴"
                        st.markdown(f"**{status_icon} {source['name']}**")
                        st.caption(f"📁 {source['path']}")
                        
                        # Show file types
                        types_str = ", ".join(source["file_types"])
                        st.caption(f"📄 Types: {types_str}")
                    
                    with col2:
                        st.caption(f"**Status:** {source['status'].title()}")
                        if source.get("last_scanned"):
                            last_scan = source["last_scanned"][:10]
                            st.caption(f"**Last Scan:** {last_scan}")
                        else:
                            st.caption("**Last Scan:** Never")
                        
                        files_processed = source.get("files_processed", 0)
                        st.caption(f"**Files Processed:** {files_processed}")
                    
                    with col3:
                        # Toggle enabled/disabled
                        new_enabled = st.checkbox(
                            "Enabled",
                            value=source["enabled"],
                            key=f"enabled_{source['id']}"
                        )
                        
                        if new_enabled != source["enabled"]:
                            self.manager.update_source(source["id"], {"enabled": new_enabled})
                            st.rerun()
                    
                    with col4:
                        # Action buttons
                        if st.button("🗑️", key=f"delete_{source['id']}", help="Delete source"):
                            if self.manager.remove_source(source["id"]):
                                st.success("✅ Source removed")
                                st.rerun()
                        
                        if st.button("🔍", key=f"scan_{source['id']}", help="Scan this source"):
                            st.session_state[f"scan_source_{source['id']}"] = True
                            st.rerun()

                        if st.button("👁️", key=f"preview_{source['id']}", help="Preview what files would be processed"):
                            st.session_state[f"preview_source_{source['id']}"] = True
                            st.rerun()
                    
                    # Handle individual source scanning
                    if st.session_state.get(f"scan_source_{source['id']}", False):
                        st.session_state[f"scan_source_{source['id']}"] = False

                        with st.spinner(f"Processing {source['name']}..."):
                            result = self.manager.run_bulk_ingestion(
                                source["path"],
                                source["file_types"],
                                dry_run=False
                            )

                        self._display_scan_result(source["name"], result, dry_run=False)

                    # Handle individual source preview
                    if st.session_state.get(f"preview_source_{source['id']}", False):
                        st.session_state[f"preview_source_{source['id']}"] = False

                        with st.spinner(f"Analyzing {source['name']}..."):
                            preview = self.manager.get_source_preview(
                                source["path"],
                                source["file_types"]
                            )

                        if preview["success"]:
                            st.success(f"📊 Analysis complete for {source['name']}")

                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("📄 New Files", preview["new_files"])
                            with col2:
                                st.metric("⏭️ Already Processed", preview["already_processed"])
                            with col3:
                                st.metric("📊 Total Found", preview["total_found"])
                            with col4:
                                if preview["total_found"] > 0:
                                    new_pct = (preview["new_files"] / preview["total_found"]) * 100
                                    st.metric("🆕 New %", f"{new_pct:.1f}%")
                                else:
                                    st.metric("🆕 New %", "0%")

                            if preview["new_files"] > 0:
                                st.info(f"✨ {preview['new_files']} new files ready to process!")
                                if st.button(f"🚀 Process {preview['new_files']} new files", key=f"process_new_{source['id']}"):
                                    with st.spinner(f"Processing {preview['new_files']} new files..."):
                                        result = self.manager.run_bulk_ingestion(
                                            source["path"],
                                            source["file_types"],
                                            dry_run=False
                                        )
                                    self._display_scan_result(source["name"], result, dry_run=False)
                            else:
                                st.info("✅ All files in this source have already been processed!")
                        else:
                            st.error(f"❌ Failed to analyze {source['name']}")
                            if preview["stderr"]:
                                st.error(preview["stderr"])

                    st.divider()
        else:
            st.info("📝 No sources configured. Add a source above to get started.")

    def _validate_path(self, path_str: str) -> Dict[str, Any]:
        """Enhanced cross-platform path validation with Docker support."""
        import os
        import platform

        try:
            # Clean and normalize the path
            cleaned_path = path_str.strip()
            original_path = cleaned_path

            # Check if running in Docker
            is_docker = os.environ.get('SAM_DOCKER', 'false').lower() == 'true'

            if is_docker:
                # Handle Docker path mapping for Windows paths
                cleaned_path = self._map_docker_path(cleaned_path)
            else:
                # Handle different path formats for native execution
                if platform.system() == "Windows":
                    # Handle Windows paths
                    if cleaned_path.startswith("/") and not cleaned_path.startswith("//"):
                        # Convert Unix-style path to Windows if needed
                        cleaned_path = cleaned_path.replace("/", "\\")

                    # Expand environment variables
                    cleaned_path = os.path.expandvars(cleaned_path)

                else:
                    # Handle Unix-like systems (macOS, Linux)
                    # Expand user home directory (~)
                    cleaned_path = os.path.expanduser(cleaned_path)

                    # Expand environment variables
                    cleaned_path = os.path.expandvars(cleaned_path)

            # Create Path object and resolve
            path_obj = Path(cleaned_path).resolve()

            # Check if path exists
            exists = path_obj.exists()
            is_directory = path_obj.is_dir() if exists else False

            # Additional checks for common issues
            error_details = []

            if not exists:
                # Check parent directory
                parent = path_obj.parent
                if parent.exists():
                    error_details.append(f"Parent directory exists: {parent}")
                    if is_docker and original_path != cleaned_path:
                        error_details.append(f"Docker path mapping applied: {original_path} -> {cleaned_path}")
                        error_details.append("Make sure the host directory is mounted in docker-compose.yml")
                        error_details.append("Example: - C:\\Users:/app/host_users:ro")
                    else:
                        error_details.append("Path might be a typo or the directory needs to be created")
                else:
                    error_details.append(f"Parent directory does not exist: {parent}")
                    if is_docker and original_path != cleaned_path:
                        error_details.append(f"Docker path mapping applied: {original_path} -> {cleaned_path}")
                        error_details.append("Host directory not mounted or mapping incorrect")

                # Check for case sensitivity issues (common on macOS)
                if platform.system() == "Darwin":  # macOS
                    try:
                        # Try to find similar paths with different case
                        parent_contents = list(parent.iterdir()) if parent.exists() else []
                        similar_names = [
                            p.name for p in parent_contents
                            if p.name.lower() == path_obj.name.lower()
                        ]
                        if similar_names:
                            error_details.append(f"Similar names found (case mismatch): {similar_names}")
                    except:
                        pass

            elif exists and not is_directory:
                error_details.append("Path exists but is not a directory")

            # Check permissions
            if exists and is_directory:
                try:
                    # Test read permission
                    list(path_obj.iterdir())
                    readable = True
                except PermissionError:
                    readable = False
                    error_details.append("Directory exists but is not readable (permission denied)")
                except:
                    readable = False
                    error_details.append("Directory exists but cannot be accessed")
            else:
                readable = False

            # Determine if path is valid
            valid = exists and is_directory and readable

            if valid:
                return {
                    "valid": True,
                    "normalized_path": str(path_obj),
                    "exists": exists,
                    "is_directory": is_directory,
                    "readable": readable,
                    "platform": platform.system(),
                    "original_path": path_str,
                    "docker_mapped": is_docker and original_path != cleaned_path,
                    "mapped_path": cleaned_path if is_docker else None
                }
            else:
                error_msg = "Path validation failed"
                if not exists:
                    error_msg = "Path does not exist"
                elif not is_directory:
                    error_msg = "Path is not a directory"
                elif not readable:
                    error_msg = "Directory is not readable"

                return {
                    "valid": False,
                    "error": error_msg,
                    "normalized_path": str(path_obj),
                    "exists": exists,
                    "is_directory": is_directory,
                    "readable": readable,
                    "platform": platform.system(),
                    "original_path": path_str,
                    "docker_mapped": is_docker and original_path != cleaned_path,
                    "mapped_path": cleaned_path if is_docker else None,
                    "error_details": error_details
                }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Path validation error: {str(e)}",
                "normalized_path": cleaned_path if 'cleaned_path' in locals() else path_str,
                "exists": False,
                "is_directory": False,
                "readable": False,
                "platform": platform.system(),
                "original_path": path_str,
                "error_details": [f"Exception: {str(e)}"]
            }

    def _map_docker_path(self, windows_path: str) -> str:
        """Map Windows host paths to Docker container paths."""
        import re

        # Normalize Windows path separators
        normalized_path = windows_path.replace("\\", "/")

        # Common Windows to Docker path mappings
        path_mappings = {
            r"^C:/Users": "/app/host_users",
            r"^c:/users": "/app/host_users",  # lowercase variant
            r"^/c/users": "/app/host_users",  # Git Bash style
            # Add more mappings as needed
        }

        for pattern, replacement in path_mappings.items():
            if re.match(pattern, normalized_path, re.IGNORECASE):
                # Replace the matched pattern
                mapped_path = re.sub(pattern, replacement, normalized_path, flags=re.IGNORECASE)
                return mapped_path

        # If no mapping found, return original path
        # This might be a path already inside the container
        return normalized_path

    def _run_bulk_operation(self, sources: List[Dict], dry_run: bool):
        """Run bulk operation on multiple sources from source management."""
        if not sources:
            st.warning("⚠️ No enabled sources to process")
            return

        operation_type = "Preview" if dry_run else "Processing"
        st.info(f"🚀 {operation_type} {len(sources)} source(s)...")

        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.container()

        total_sources = len(sources)
        successful = 0
        failed = 0

        for i, source in enumerate(sources):
            progress = (i + 1) / total_sources
            progress_bar.progress(progress)
            status_text.text(f"{operation_type} {source['name']} ({i+1}/{total_sources})")

            result = self.manager.run_bulk_ingestion(
                source["path"],
                source["file_types"],
                dry_run
            )

            if result["success"]:
                successful += 1
            else:
                failed += 1

            with results_container:
                self._display_scan_result(source["name"], result, dry_run)

        # Final summary
        status_text.text(f"✅ {operation_type} completed: {successful} successful, {failed} failed")
        progress_bar.progress(1.0)

        if not dry_run and successful > 0:
            st.success(f"🎉 {successful} source(s) processed successfully! Files have been added to SAM's knowledge base.")

            # Trigger knowledge consolidation
            if st.button("🧠 Consolidate Knowledge", type="primary", key="consolidate_knowledge_button", help="Run knowledge consolidation to optimize SAM's memory"):
                self._trigger_knowledge_consolidation()

    def _trigger_knowledge_consolidation(self):
        """Trigger knowledge consolidation after successful processing."""
        try:
            with st.spinner("🧠 Running knowledge consolidation..."):
                # Import and run knowledge consolidation
                from memory.knowledge_consolidation import run_knowledge_consolidation

                result = run_knowledge_consolidation()

                if result.get("success", False):
                    st.success("✅ Knowledge consolidation completed successfully!")
                    st.info(f"📊 Consolidated {result.get('memories_processed', 0)} memories")

                    # Show consolidation metrics
                    if result.get("metrics"):
                        metrics = result["metrics"]
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Memories Processed", metrics.get("total_memories", 0))
                        with col2:
                            st.metric("Summaries Created", metrics.get("summaries_created", 0))
                        with col3:
                            st.metric("Quality Score", f"{metrics.get('avg_quality', 0):.2f}")
                else:
                    st.warning("⚠️ Knowledge consolidation completed with warnings")
                    if result.get("message"):
                        st.info(result["message"])

        except ImportError:
            st.warning("⚠️ Knowledge consolidation not available - feature may not be implemented yet")
        except Exception as e:
            st.error(f"❌ Knowledge consolidation failed: {e}")

    def _render_manual_scan(self):
        """Render the manual scan interface."""
        st.markdown("### 🚀 Manual Scan Operations")
        st.markdown("Trigger bulk ingestion scans manually")

        # Enhanced incremental processing information with detailed benefits
        st.info("💡 **Smart Incremental Processing:** SAM only processes new or modified files, automatically skipping files that have already been processed. This makes subsequent scans much faster!")

        # Add detailed incremental processing benefits
        with st.expander("🔍 How Incremental Processing Works", expanded=False):
            st.markdown("""
            **🧠 Intelligent File Tracking:**
            - **SHA256 Hash Verification**: Each file's content is hashed to detect any changes
            - **Modification Time Checking**: File timestamps are compared to detect updates
            - **SQLite State Database**: Persistent tracking of all processed files
            - **Cross-Session Memory**: Remembers processed files between SAM restarts

            **⚡ Performance Benefits:**
            - **Skip Unchanged Files**: Dramatically reduces processing time on subsequent scans
            - **Process Only New Content**: Focus computational resources on new information
            - **Efficient Resource Usage**: Avoid redundant processing of existing knowledge
            - **Faster Iteration**: Quick re-scans when adding new documents to existing folders

            **🔄 What Triggers Re-Processing:**
            - ✅ **New files** added to watched folders
            - ✅ **Modified files** (content or metadata changes)
            - ✅ **Renamed files** (treated as new files)
            - ⏭️ **Unchanged files** are automatically skipped

            **📊 Efficiency Metrics:**
            - View real-time statistics showing files processed vs. skipped
            - Track processing efficiency over time
            - Monitor storage and computational savings
            """)

        # Add incremental processing status overview
        try:
            # Get overall statistics from the state database
            if self.manager.state_db.exists():
                with sqlite3.connect(self.manager.state_db) as conn:
                    cursor = conn.execute("SELECT COUNT(*) as total, SUM(chunks_created) as total_chunks, AVG(enrichment_score) as avg_score FROM processed_files WHERE status = 'success'")
                    stats = cursor.fetchone()

                    if stats and stats[0] > 0:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📄 Total Processed Files", f"{stats[0]:,}")
                        with col2:
                            st.metric("🧩 Total Memory Chunks", f"{stats[1] or 0:,}")
                        with col3:
                            avg_score = stats[2] or 0
                            st.metric("⭐ Avg Enrichment Score", f"{avg_score:.2f}")

                        st.success(f"✅ **Incremental Processing Active**: {stats[0]:,} files already in knowledge base - only new/modified files will be processed!")
        except Exception as e:
            # Graceful fallback if database access fails
            st.info("📊 Incremental processing database initializing...")

        config = self.manager.load_config()
        sources = config.get("sources", [])
        enabled_sources = [s for s in sources if s["enabled"]]
        
        if not enabled_sources:
            st.warning("⚠️ No enabled sources found. Please add and enable sources first.")
            return
        
        # Scan all sources
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 🔄 Scan All Sources")
            st.markdown("Process all enabled sources in sequence")

            col1a, col1b = st.columns(2)

            with col1a:
                if st.button("👁️ Preview All", key="preview_all_sources_button_manual", help="See what files would be processed across all sources"):
                    self._preview_all_sources(enabled_sources)

            with col1b:
                dry_run_all = st.checkbox("Dry Run", key="dry_run_all", help="Preview only, don't actually process")

            if st.button("🚀 Scan All Sources", type="primary", key="scan_all_sources_button"):
                self._run_scan_all(enabled_sources, dry_run_all)
        
        with col2:
            st.markdown("#### ⚡ Quick Actions")
            
            if st.button("📊 View Statistics", key="view_statistics_button"):
                st.session_state.show_stats = True

            if st.button("📋 View Logs", key="view_logs_button"):
                self._show_logs()
        
        # Individual source scanning
        st.markdown("#### 📂 Scan Individual Sources")
        
        for source in enabled_sources:
            with st.expander(f"🔍 {source['name']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Path:** `{source['path']}`")
                    st.markdown(f"**File Types:** {', '.join(source['file_types'])}")
                    
                    dry_run = st.checkbox(
                        "Dry Run (Preview Only)",
                        key=f"dry_run_{source['id']}"
                    )
                
                with col2:
                    col2a, col2b = st.columns(2)

                    with col2a:
                        if st.button(
                            "👁️ Preview",
                            key=f"preview_btn_{source['id']}",
                            help="See what files would be processed"
                        ):
                            self._show_source_preview(source)

                    with col2b:
                        if st.button(
                            "🚀 Scan",
                            key=f"scan_btn_{source['id']}",
                            type="secondary"
                        ):
                            self._run_individual_scan(source, dry_run)
        
        # Check for scan triggers from source management
        for source in sources:
            if st.session_state.get(f"scan_source_{source['id']}", False):
                st.session_state[f"scan_source_{source['id']}"] = False
                self._run_individual_scan(source, dry_run=True)
    
    def _run_scan_all(self, sources: List[Dict], dry_run: bool):
        """Run scan for all sources."""
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.container()
        
        total_sources = len(sources)
        
        for i, source in enumerate(sources):
            progress = (i + 1) / total_sources
            progress_bar.progress(progress)
            status_text.text(f"Scanning {source['name']} ({i+1}/{total_sources})")
            
            result = self.manager.run_bulk_ingestion(
                source["path"],
                source["file_types"],
                dry_run
            )
            
            with results_container:
                self._display_scan_result(source["name"], result, dry_run)
        
        status_text.text("✅ All scans completed!")
        progress_bar.progress(1.0)
    
    def _show_source_preview(self, source: Dict):
        """Show preview of what files would be processed for a source."""
        with st.spinner(f"Analyzing {source['name']}..."):
            preview = self.manager.get_source_preview(
                source["path"],
                source["file_types"]
            )

        if preview["success"]:
            st.success(f"📊 Analysis complete for {source['name']}")

            # Show metrics with efficiency information
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📄 Total Found", preview["total_found"])
            with col2:
                st.metric("🆕 New/Modified", preview["new_files"],
                         help="Files that need processing")
            with col3:
                st.metric("⏭️ Already Processed", preview["already_processed"],
                         help="Files skipped due to incremental processing")
            with col4:
                if preview["total_found"] > 0:
                    efficiency = (preview["already_processed"] / preview["total_found"]) * 100
                    st.metric("⚡ Efficiency", f"{efficiency:.1f}%",
                             help="Percentage of files skipped")
                else:
                    st.metric("⚡ Efficiency", "0%")

            # Enhanced efficiency message with detailed benefits
            if preview["already_processed"] > 0:
                time_saved_estimate = preview["already_processed"] * 2  # Estimate 2 minutes per file
                st.info(f"⚡ **Incremental Processing Benefit:** {preview['already_processed']} files already processed and will be skipped, saving approximately {time_saved_estimate} minutes of processing time!")

                # Add detailed breakdown using container instead of nested expander
                st.markdown("**📊 Incremental Processing Details:**")
                with st.container():
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Files to Process:**")
                        st.markdown(f"- 🆕 New files: {preview['new_files']}")
                        st.markdown(f"- ⏭️ Already processed: {preview['already_processed']}")
                        st.markdown(f"- 📊 Total discovered: {preview['total_found']}")

                    with col2:
                        st.markdown("**Efficiency Metrics:**")
                        if preview['total_found'] > 0:
                            efficiency_pct = (preview['already_processed'] / preview['total_found']) * 100
                            st.markdown(f"- ⚡ Skip efficiency: {efficiency_pct:.1f}%")
                            st.markdown(f"- 🕒 Est. time saved: ~{time_saved_estimate} min")
                            st.markdown(f"- 💾 Storage saved: Significant")
                        else:
                            st.markdown("- ⚡ Skip efficiency: 0%")
            else:
                if preview["new_files"] > 0:
                    st.info("🆕 **First-time processing**: All files are new and will be processed for the first time!")

            # Show action buttons based on results
            if preview["new_files"] > 0:
                st.info(f"✨ {preview['new_files']} new files ready to process!")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🔍 Dry Run {preview['new_files']} files", key=f"dry_run_new_{source['id']}"):
                        self._run_individual_scan(source, dry_run=True)

                with col2:
                    if st.button(f"🚀 Process {preview['new_files']} files", key=f"process_new_{source['id']}", type="primary"):
                        self._run_individual_scan(source, dry_run=False)
            else:
                st.info("✅ All files in this source have already been processed!")

                # Enhanced options with recently processed files view using container instead of nested expander
                st.markdown("**📋 Recently Processed Files & Options:**")
                with st.container():
                    # Show recently processed files from this source
                    try:
                        if self.manager.state_db.exists():
                            with sqlite3.connect(self.manager.state_db) as conn:
                                cursor = conn.execute("""
                                    SELECT filepath, processed_at, chunks_created, enrichment_score, status
                                    FROM processed_files
                                    WHERE filepath LIKE ?
                                    ORDER BY processed_at DESC
                                    LIMIT 10
                                """, (f"{source['path']}%",))
                                recent_files = cursor.fetchall()

                                if recent_files:
                                    st.markdown("**🕒 Recently Processed Files:**")
                                    for filepath, processed_at, chunks, score, status in recent_files:
                                        filename = Path(filepath).name
                                        status_icon = "✅" if status == "success" else "❌"
                                        try:
                                            # Parse timestamp
                                            dt = datetime.fromisoformat(processed_at)
                                            time_str = dt.strftime("%Y-%m-%d %H:%M")
                                        except:
                                            time_str = processed_at[:16] if processed_at else "Unknown"

                                        st.markdown(f"  {status_icon} `{filename}` - {time_str} ({chunks} chunks, score: {score:.2f})")
                                else:
                                    st.markdown("**📄 No files found in processing history for this source.**")
                    except Exception as e:
                        st.markdown("**📊 Processing history unavailable.**")

                    st.markdown("---")
                    st.markdown("**🔄 Available Options:**")
                    st.markdown("- **Add new files** to the source folder")
                    st.markdown("- **Modify existing files** (they will be automatically re-processed)")
                    st.markdown("- **Check other sources** for new content")
                    st.markdown("- **Force re-processing** using the advanced options below")

                    # Advanced re-processing options
                    st.markdown("**⚙️ Advanced Options:**")
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("🔄 Force Re-scan", key=f"force_rescan_{source['id']}",
                                   help="Clear processing history and re-scan all files"):
                            if st.session_state.get(f"confirm_rescan_{source['id']}", False):
                                # Clear processing history for this source
                                try:
                                    if self.manager.state_db.exists():
                                        with sqlite3.connect(self.manager.state_db) as conn:
                                            conn.execute("DELETE FROM processed_files WHERE filepath LIKE ?", (f"{source['path']}%",))
                                            conn.commit()
                                        st.success(f"✅ Processing history cleared for {source['name']}. All files will be re-processed on next scan.")
                                        st.session_state[f"confirm_rescan_{source['id']}"] = False
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Failed to clear processing history: {e}")
                            else:
                                st.session_state[f"confirm_rescan_{source['id']}"] = True
                                st.warning("⚠️ Click again to confirm clearing processing history")

                    with col2:
                        if st.button("📊 View Source Stats", key=f"view_stats_{source['id']}",
                                   help="View detailed statistics for this source"):
                            self._show_source_statistics(source)
        else:
            st.error(f"❌ Failed to analyze {source['name']}")
            if preview["stderr"]:
                st.error(preview["stderr"])

    def _run_individual_scan(self, source: Dict, dry_run: bool):
        """Run scan for an individual source."""
        with st.spinner(f"{'Previewing' if dry_run else 'Processing'} {source['name']}..."):
            result = self.manager.run_bulk_ingestion(
                source["path"],
                source["file_types"],
                dry_run
            )

            # Display result without nested expanders (we're already inside one)
            self._display_scan_result(source["name"], result, dry_run, use_expander=False)
    
    def _display_scan_result(self, source_name: str, result: Dict, dry_run: bool, use_expander: bool = True):
        """Display the result of a scan operation with enhanced incremental processing information."""
        if result["success"]:
            st.success(f"✅ {source_name}: Scan completed successfully")

            # Parse output for summary and extract key metrics
            stdout = result["stdout"]
            processed_count = 0
            skipped_count = 0
            failed_count = 0
            total_found = 0

            # Extract metrics from output
            if "Bulk Ingestion Summary:" in stdout:
                lines = stdout.split('\n')
                for line in lines:
                    if "Processed:" in line:
                        try:
                            processed_count = int(line.split(':')[1].strip())
                        except:
                            pass
                    elif "Skipped:" in line:
                        try:
                            skipped_count = int(line.split(':')[1].strip())
                        except:
                            pass
                    elif "Failed:" in line:
                        try:
                            failed_count = int(line.split(':')[1].strip())
                        except:
                            pass
                    elif "Total found:" in line:
                        try:
                            total_found = int(line.split(':')[1].strip())
                        except:
                            pass

            # Display enhanced metrics if we have data
            if total_found > 0:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📄 Total Found", total_found)

                with col2:
                    st.metric("🆕 New/Modified", processed_count,
                             help="Files that will be or were processed")

                with col3:
                    st.metric("⏭️ Already Processed", skipped_count,
                             help="Files skipped because they haven't changed")

                with col4:
                    efficiency = (skipped_count / total_found * 100) if total_found > 0 else 0
                    st.metric("⚡ Efficiency", f"{efficiency:.1f}%",
                             help="Percentage of files skipped due to incremental processing")

                # Show efficiency message
                if skipped_count > 0:
                    st.info(f"⚡ **Incremental Processing Benefit:** Skipped {skipped_count} unchanged files, saving significant processing time!")

            # Show detailed output in expander
            if "Bulk Ingestion Summary:" in stdout:
                summary_start = stdout.find("Bulk Ingestion Summary:")
                summary_section = stdout[summary_start:summary_start+500]

                if use_expander:
                    # Use container with markdown header instead of nested expander
                    st.markdown(f"**📊 {source_name} Detailed Results:**")
                    with st.container():
                        st.code(summary_section)

                        if dry_run:
                            st.info("🔍 This was a dry run - no files were actually processed")
                else:
                    # Display directly without expander (we're already inside one)
                    st.markdown(f"**📊 {source_name} Detailed Results:**")
                    st.code(summary_section)

                    if dry_run:
                        st.info("🔍 This was a dry run - no files were actually processed")

        else:
            st.error(f"❌ {source_name}: Scan failed")

            if use_expander:
                # Use container with markdown header instead of nested expander
                st.markdown(f"**🔍 {source_name} Error Details:**")
                with st.container():
                    if result["stderr"]:
                        st.code(result["stderr"])
                    if result["stdout"]:
                        st.code(result["stdout"])
            else:
                # Display directly without expander
                st.markdown(f"**🔍 {source_name} Error Details:**")
                if result["stderr"]:
                    st.code(result["stderr"])
                if result["stdout"]:
                    st.code(result["stdout"])
    
    def _render_statistics(self):
        """Render the statistics interface with pagination."""
        st.markdown("### 📊 Ingestion Statistics")

        # Add information about incremental processing
        with st.expander("ℹ️ About Incremental Processing", expanded=False):
            st.markdown("""
            **SAM's Smart Incremental Processing:**

            🔄 **Only New Files Processed:** SAM automatically skips files that have already been processed
            📊 **File Change Detection:** Uses SHA256 hashing and modification timestamps to detect changes
            ⚡ **Efficiency:** Dramatically reduces processing time for subsequent scans
            📈 **Statistics Tracking:** Complete history of all processed files with pagination

            **What gets processed:**
            - ✅ New files that haven't been seen before
            - ✅ Existing files that have been modified since last processing
            - ⏭️ Unchanged files are automatically skipped
            """)

        # Initialize pagination state
        if 'stats_page' not in st.session_state:
            st.session_state.stats_page = 1

        # Page size selector and refresh button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            page_size = st.selectbox(
                "Files per page",
                options=[10, 30, 50, 100],
                index=1,  # Default to 30
                key="stats_page_size"
            )

        with col2:
            st.markdown("") # Spacer

        with col3:
            if st.button("🔄 Refresh Stats", help="Reload statistics from database"):
                st.rerun()

        # Get statistics with pagination
        stats = self.manager.get_ingestion_stats(
            page=st.session_state.stats_page,
            page_size=page_size
        )

        if stats and stats['total_files'] > 0:
            # Overview metrics with pagination info
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("Total Files", stats['total_files'])

            with col2:
                st.metric("Memory Chunks", stats['total_chunks'])

            with col3:
                success_rate = f"{stats['successful']}/{stats['total_files']}"
                success_pct = (stats['successful'] / stats['total_files'] * 100) if stats['total_files'] > 0 else 0
                st.metric("Success Rate", success_rate, f"{success_pct:.1f}%")

            with col4:
                avg_score = stats['avg_enrichment']
                st.metric("Avg Enrichment", f"{avg_score:.2f}")

            with col5:
                # Pagination info as a metric
                current_page = stats['current_page']
                total_pages = stats['total_pages']
                st.metric("Page", f"{current_page} of {total_pages}")

            # Prominent pagination status
            if stats['total_pages'] > 1:
                st.info(f"📄 Showing files {((stats['current_page']-1) * stats['page_size']) + 1} to {min(stats['current_page'] * stats['page_size'], stats['total_files'])} of {stats['total_files']} total files")

            # File listing with pagination
            if stats['recent_activity']:
                # Pagination controls (top)
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

                with col1:
                    if st.button("⏮️ First", disabled=not stats['has_prev'], key="first_page"):
                        st.session_state.stats_page = 1
                        st.rerun()

                with col2:
                    if st.button("⬅️ Prev", disabled=not stats['has_prev'], key="prev_page"):
                        st.session_state.stats_page = max(1, st.session_state.stats_page - 1)
                        st.rerun()

                with col3:
                    st.markdown(f"**Page {stats['current_page']} of {stats['total_pages']}** ({stats['total_files']} total files)")

                with col4:
                    if st.button("Next ➡️", disabled=not stats['has_next'], key="next_page"):
                        st.session_state.stats_page = min(stats['total_pages'], st.session_state.stats_page + 1)
                        st.rerun()

                with col5:
                    if st.button("Last ⏭️", disabled=not stats['has_next'], key="last_page"):
                        st.session_state.stats_page = stats['total_pages']
                        st.rerun()

                st.markdown("#### 📋 Processed Files")

                # File listing
                for i, activity in enumerate(stats['recent_activity']):
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])

                        with col1:
                            filename = Path(activity['filepath']).name
                            st.markdown(f"**{filename}**")
                            st.caption(activity['filepath'])

                        with col2:
                            processed_date = activity['processed_at'][:10]
                            processed_time = activity['processed_at'][11:19]
                            st.caption(f"📅 {processed_date}")
                            st.caption(f"🕐 {processed_time}")

                        with col3:
                            status_icon = "✅" if activity['status'] == 'success' else "❌"
                            st.markdown(f"{status_icon} {activity['status']}")

                            # File size
                            file_size = activity.get('file_size', 0)
                            if file_size > 0:
                                if file_size > 1024 * 1024:
                                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                                elif file_size > 1024:
                                    size_str = f"{file_size / 1024:.1f} KB"
                                else:
                                    size_str = f"{file_size} B"
                                st.caption(f"📦 {size_str}")

                        with col4:
                            score = activity['enrichment_score']
                            st.caption(f"Score: {score:.2f}")

                            # Score indicator
                            if score >= 0.8:
                                st.caption("🟢 Excellent")
                            elif score >= 0.6:
                                st.caption("🟡 Good")
                            elif score >= 0.4:
                                st.caption("🟠 Fair")
                            else:
                                st.caption("🔴 Poor")

                        with col5:
                            chunks = activity['chunks_created']
                            st.caption(f"Chunks: {chunks}")

                            # Chunks indicator
                            if chunks > 10:
                                st.caption("📚 Large")
                            elif chunks > 5:
                                st.caption("📖 Medium")
                            elif chunks > 0:
                                st.caption("📄 Small")
                            else:
                                st.caption("❌ None")

                        st.divider()

                # Pagination controls (bottom)
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

                with col1:
                    if st.button("⏮️ First", disabled=not stats['has_prev'], key="first_page_bottom"):
                        st.session_state.stats_page = 1
                        st.rerun()

                with col2:
                    if st.button("⬅️ Prev", disabled=not stats['has_prev'], key="prev_page_bottom"):
                        st.session_state.stats_page = max(1, st.session_state.stats_page - 1)
                        st.rerun()

                with col3:
                    # Jump to page input
                    target_page = st.number_input(
                        "Jump to page:",
                        min_value=1,
                        max_value=stats['total_pages'],
                        value=stats['current_page'],
                        key="jump_to_page"
                    )
                    if st.button("Go", key="jump_page"):
                        st.session_state.stats_page = target_page
                        st.rerun()

                with col4:
                    if st.button("Next ➡️", disabled=not stats['has_next'], key="next_page_bottom"):
                        st.session_state.stats_page = min(stats['total_pages'], st.session_state.stats_page + 1)
                        st.rerun()

                with col5:
                    if st.button("Last ⏭️", disabled=not stats['has_next'], key="last_page_bottom"):
                        st.session_state.stats_page = stats['total_pages']
                        st.rerun()

        else:
            st.info("📝 No ingestion statistics available yet. Run some scans to see data here.")
    
    def _render_settings(self):
        """Render the settings interface."""
        st.markdown("### ⚙️ Bulk Ingestion Settings")
        
        config = self.manager.load_config()
        settings = config.get("settings", {})
        
        # File type defaults
        st.markdown("#### 📄 Default File Types")
        default_types = st.multiselect(
            "Default file types for new sources",
            options=["pdf", "txt", "md", "docx", "doc", "py", "js", "html", "json", "csv", "xml", "yaml"],
            default=settings.get("default_file_types", ["pdf", "txt", "md"]),
            help="These file types will be pre-selected when adding new sources"
        )
        
        # Processing limits
        st.markdown("#### 🔧 Processing Limits")
        col1, col2 = st.columns(2)
        
        with col1:
            max_file_size = st.number_input(
                "Max File Size (MB)",
                min_value=1,
                max_value=1000,
                value=settings.get("max_file_size_mb", 100),
                help="Maximum file size to process"
            )
        
        with col2:
            enable_notifications = st.checkbox(
                "Enable Notifications",
                value=settings.get("enable_notifications", True),
                help="Show notifications when scans complete"
            )
        
        # Save settings
        if st.button("💾 Save Settings", type="primary"):
            settings.update({
                "default_file_types": default_types,
                "max_file_size_mb": max_file_size,
                "enable_notifications": enable_notifications
            })
            
            config["settings"] = settings
            self.manager.save_config(config)
            st.success("✅ Settings saved successfully!")
    
    def _show_source_statistics(self, source):
        """Show detailed statistics for a specific source."""
        st.markdown(f"### 📊 Statistics for {source['name']}")

        try:
            if self.manager.state_db.exists():
                with sqlite3.connect(self.manager.state_db) as conn:
                    # Get overall stats for this source
                    cursor = conn.execute("""
                        SELECT
                            COUNT(*) as total_files,
                            SUM(chunks_created) as total_chunks,
                            AVG(enrichment_score) as avg_score,
                            MIN(processed_at) as first_processed,
                            MAX(processed_at) as last_processed,
                            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed
                        FROM processed_files
                        WHERE filepath LIKE ?
                    """, (f"{source['path']}%",))

                    stats = cursor.fetchone()

                    if stats and stats[0] > 0:
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric("📄 Total Files", f"{stats[0]:,}")
                            st.metric("✅ Successful", f"{stats[5]:,}")

                        with col2:
                            st.metric("🧩 Total Chunks", f"{stats[1] or 0:,}")
                            st.metric("❌ Failed", f"{stats[6]:,}")

                        with col3:
                            avg_score = stats[2] or 0
                            st.metric("⭐ Avg Score", f"{avg_score:.2f}")
                            success_rate = (stats[5] / stats[0]) * 100 if stats[0] > 0 else 0
                            st.metric("📈 Success Rate", f"{success_rate:.1f}%")

                        with col4:
                            try:
                                first_dt = datetime.fromisoformat(stats[3]) if stats[3] else None
                                last_dt = datetime.fromisoformat(stats[4]) if stats[4] else None

                                if first_dt:
                                    st.metric("🕒 First Processed", first_dt.strftime("%Y-%m-%d"))
                                if last_dt:
                                    st.metric("🕒 Last Processed", last_dt.strftime("%Y-%m-%d"))
                            except:
                                st.metric("🕒 Processing Period", "Available")

                        # Show file type breakdown
                        cursor = conn.execute("""
                            SELECT
                                CASE
                                    WHEN filepath LIKE '%.pdf' THEN 'PDF'
                                    WHEN filepath LIKE '%.docx' OR filepath LIKE '%.doc' THEN 'Word'
                                    WHEN filepath LIKE '%.txt' OR filepath LIKE '%.md' THEN 'Text'
                                    WHEN filepath LIKE '%.pptx' OR filepath LIKE '%.ppt' THEN 'PowerPoint'
                                    ELSE 'Other'
                                END as file_type,
                                COUNT(*) as count,
                                SUM(chunks_created) as chunks
                            FROM processed_files
                            WHERE filepath LIKE ? AND status = 'success'
                            GROUP BY file_type
                            ORDER BY count DESC
                        """, (f"{source['path']}%",))

                        file_types = cursor.fetchall()

                        if file_types:
                            st.markdown("**📁 File Type Breakdown:**")
                            for file_type, count, chunks in file_types:
                                st.markdown(f"- **{file_type}**: {count} files ({chunks or 0} chunks)")
                    else:
                        st.info("No processing statistics available for this source.")
            else:
                st.info("Processing database not found.")
        except Exception as e:
            st.error(f"Failed to load statistics: {e}")

    def _show_logs(self):
        """Display recent logs."""
        try:
            if self.manager.log_file.exists():
                with open(self.manager.log_file, 'r') as f:
                    logs = f.read()

                # Show last 50 lines
                log_lines = logs.split('\n')[-50:]
                recent_logs = '\n'.join(log_lines)

                st.code(recent_logs, language="text")
            else:
                st.info("📝 No log file found yet.")
        except Exception as e:
            st.error(f"Error reading logs: {e}")

    def _render_discovery_cycle(self):
        """Render the automated discovery cycle interface."""
        st.subheader("🔬 Automated Discovery Cycle")
        st.markdown("*Automated research discovery and insight synthesis pipeline*")

        # Import discovery cycle components
        try:
            from sam.orchestration.discovery_cycle import get_discovery_orchestrator, DiscoveryStage
            from sam.state.state_manager import get_state_manager

            orchestrator = get_discovery_orchestrator()
            state_manager = get_state_manager()

            # Check current cycle status
            is_running = orchestrator.is_cycle_running()
            current_progress = orchestrator.get_current_progress()
            insights_status = orchestrator.get_new_insights_status()

            # Status display
            col1, col2, col3 = st.columns(3)

            with col1:
                if is_running:
                    st.error("🔄 **Discovery Cycle Running**")
                    if current_progress:
                        st.progress(current_progress.progress_percentage / 100.0)
                        st.caption(f"Stage: {current_progress.stage.value}")
                        st.caption(f"Step: {current_progress.current_step}")
                else:
                    st.success("✅ **Discovery Cycle Ready**")

            with col2:
                if insights_status.get('new_insights_available'):
                    st.warning("💡 **New Insights Available**")
                    timestamp = insights_status.get('last_insights_timestamp')
                    if timestamp:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(timestamp)
                            st.caption(f"Generated: {dt.strftime('%Y-%m-%d %H:%M')}")
                        except:
                            st.caption("Recently generated")
                else:
                    st.info("🔍 **No New Insights**")

            with col3:
                # Quick stats
                try:
                    from pathlib import Path
                    results_dir = Path("logs/discovery_cycles")
                    if results_dir.exists():
                        cycle_files = list(results_dir.glob("*.json"))
                        st.metric("🔄 Total Cycles", len(cycle_files))
                    else:
                        st.metric("🔄 Total Cycles", 0)
                except:
                    st.metric("🔄 Total Cycles", "N/A")

            st.markdown("---")

            # Discovery cycle explanation
            with st.expander("ℹ️ What is the Discovery Cycle?", expanded=False):
                st.markdown("""
                **The Automated Discovery Cycle is SAM's research automation engine:**

                🔄 **Complete Pipeline:**
                1. **Bulk Ingestion**: Process all configured document sources
                2. **Dream Canvas Clustering**: Analyze memory patterns and find concept clusters
                3. **Insight Synthesis**: Generate new insights from discovered patterns
                4. **Research Initiation**: Automatically trigger research for promising insights

                🎯 **Benefits:**
                - **Automated Knowledge Discovery**: Find hidden patterns in your data
                - **Research Automation**: Automatically discover relevant papers
                - **Insight Generation**: Synthesize new understanding from existing knowledge
                - **Continuous Learning**: Keep SAM's knowledge current and expanding

                🛡️ **Security:**
                - All downloads go to quarantine for vetting
                - Multi-dimensional analysis (security, relevance, credibility)
                - Manual review options for sensitive content
                - Full audit trail and logging
                """)

            # Main action button
            st.markdown("### 🚀 Discovery Cycle Control")

            if not is_running:
                col1, col2 = st.columns([2, 1])

                with col1:
                    if st.button("🚀 **Start Discovery Cycle**", type="primary", use_container_width=True,
                               help="Begin automated discovery: bulk ingestion → clustering → synthesis → research"):
                        # Trigger discovery cycle
                        st.session_state.trigger_discovery_cycle = True
                        st.rerun()

                with col2:
                    if st.button("🔍 Preview Sources", use_container_width=True,
                               help="Preview what sources will be processed"):
                        st.session_state.show_discovery_preview = True

                # Handle discovery cycle trigger
                if st.session_state.get("trigger_discovery_cycle", False):
                    st.session_state.trigger_discovery_cycle = False
                    self._run_discovery_cycle(orchestrator)

                # Handle preview trigger
                if st.session_state.get("show_discovery_preview", False):
                    st.session_state.show_discovery_preview = False
                    self._show_discovery_preview(orchestrator)

            else:
                # Show progress details
                st.warning("🔄 **Discovery cycle is currently running...**")

                if current_progress:
                    progress_col1, progress_col2 = st.columns(2)

                    with progress_col1:
                        st.metric("Current Stage", current_progress.stage.value.replace('_', ' ').title())
                        st.metric("Progress", f"{current_progress.progress_percentage:.1f}%")

                    with progress_col2:
                        st.metric("Steps Completed", len(current_progress.steps_completed))
                        if current_progress.errors:
                            st.metric("Errors", len(current_progress.errors))

                    # Progress bar with details
                    st.progress(current_progress.progress_percentage / 100.0)
                    st.caption(f"**Current Step:** {current_progress.current_step}")

                    # Show completed steps using container instead of nested expander
                    if current_progress.steps_completed:
                        st.markdown("**✅ Completed Steps:**")
                        with st.container():
                            for step in current_progress.steps_completed:
                                st.success(f"✅ {step}")

                    # Show errors if any using container instead of nested expander
                    if current_progress.errors:
                        st.markdown("**⚠️ Errors:**")
                        with st.container():
                            for error in current_progress.errors:
                                st.error(f"❌ {error}")

                # Refresh button
                if st.button("🔄 Refresh Status", use_container_width=True):
                    st.rerun()

            # Recent cycles history
            st.markdown("---")
            st.markdown("### 📊 Recent Discovery Cycles")
            self._show_recent_cycles()

        except ImportError as e:
            st.error(f"❌ Discovery cycle components not available: {e}")
            st.info("💡 Make sure all Task 27 components are properly installed.")
        except Exception as e:
            st.error(f"❌ Error loading discovery cycle interface: {e}")

    def _run_discovery_cycle(self, orchestrator):
        """Run the discovery cycle asynchronously."""
        import asyncio
        import threading

        def run_cycle():
            """Run the discovery cycle in a separate thread."""
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Run the discovery cycle
                result = loop.run_until_complete(orchestrator.run_full_cycle())

                # Store result in session state
                st.session_state.discovery_cycle_result = result

            except Exception as e:
                st.session_state.discovery_cycle_error = str(e)
            finally:
                loop.close()

        # Start the cycle in a background thread
        thread = threading.Thread(target=run_cycle, daemon=True)
        thread.start()

        st.success("🚀 **Discovery cycle started!** The process is running in the background.")
        st.info("🔄 **Refresh this page** to see progress updates.")
        st.markdown("**The discovery cycle includes:**")
        st.markdown("1. 📁 **Bulk Ingestion** - Process all configured sources")
        st.markdown("2. 🧠 **Dream Canvas Clustering** - Analyze memory patterns")
        st.markdown("3. 💡 **Insight Synthesis** - Generate new insights")
        st.markdown("4. 🔬 **Research Initiation** - Trigger automated research")

    def _show_discovery_preview(self, orchestrator):
        """Show preview of what the discovery cycle will process."""
        st.info("🔍 **Discovery Cycle Preview**")

        try:
            # Get configured sources
            sources = orchestrator._get_configured_sources()

            if sources:
                st.markdown("**📁 Sources that will be processed:**")
                for i, source in enumerate(sources, 1):
                    from pathlib import Path
                    source_path = Path(source)
                    if source_path.exists():
                        file_count = len(list(source_path.rglob("*.*")))
                        st.markdown(f"{i}. **{source}** ({file_count} files)")
                    else:
                        st.markdown(f"{i}. **{source}** (⚠️ path not found)")
            else:
                st.warning("⚠️ No sources configured for bulk ingestion.")
                st.info("💡 Add sources in the 'Source Management' tab first.")

        except Exception as e:
            st.error(f"❌ Error previewing sources: {e}")

    def _show_recent_cycles(self):
        """Show recent discovery cycle results."""
        try:
            from pathlib import Path
            import json

            results_dir = Path("logs/discovery_cycles")
            if not results_dir.exists():
                st.info("📝 No discovery cycles have been run yet.")
                return

            # Get recent cycle files
            cycle_files = sorted(
                results_dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:5]  # Show last 5 cycles

            if not cycle_files:
                st.info("📝 No discovery cycle results found.")
                return

            for cycle_file in cycle_files:
                try:
                    with open(cycle_file, 'r') as f:
                        result = json.load(f)

                    # Create expandable section for each cycle
                    cycle_id = result.get('cycle_id', 'Unknown')
                    status = result.get('status', 'Unknown')
                    insights = result.get('insights_generated', 0)

                    status_emoji = "✅" if status == "completed" else "❌" if status == "failed" else "🔄"

                    # Use container with markdown header instead of nested expander
                    st.markdown(f"**{status_emoji} {cycle_id} - {status} ({insights} insights)**")
                    with st.container():
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown(f"**Status:** {status}")
                            st.markdown(f"**Insights Generated:** {insights}")
                            st.markdown(f"**Started:** {result.get('started_at', 'Unknown')}")
                            st.markdown(f"**Completed:** {result.get('completed_at', 'Unknown')}")

                        with col2:
                            stages = result.get('stages_completed', [])
                            st.markdown(f"**Stages Completed:** {len(stages)}")
                            for stage in stages:
                                st.markdown(f"✅ {stage}")

                            errors = result.get('errors', [])
                            if errors:
                                st.markdown(f"**Errors:** {len(errors)}")
                                for error in errors:
                                    st.markdown(f"❌ {error}")

                except Exception as e:
                    st.error(f"Error reading cycle file {cycle_file}: {e}")

        except Exception as e:
            st.error(f"Error loading recent cycles: {e}")

def render_bulk_ingestion():
    """Main function to render the bulk ingestion UI."""
    ui = BulkIngestionUI()
    ui.render()
