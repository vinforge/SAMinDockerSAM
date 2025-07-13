"""
Procedural Memory UI for SAM Memory Control Center
=================================================

Provides a comprehensive Streamlit interface for managing procedures,
workflows, and "how-to" guides with advanced editing capabilities.

Features:
- Two-panel layout (procedure list + editor)
- Advanced search and filtering
- Dynamic step management with reordering
- Parameter editor for reusable procedures
- Usage analytics and statistics

Author: SAM Development Team
Version: 2.0.0
"""

import streamlit as st
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ProceduralMemoryUI:
    """Streamlit UI for procedural memory management."""
    
    def __init__(self):
        """Initialize the procedural memory UI."""
        self.store = None
        self._init_store()
    
    def _init_store(self):
        """Initialize the procedural memory store."""
        try:
            from sam.memory.procedural_memory import get_procedural_memory_store
            self.store = get_procedural_memory_store()
            logger.info("Procedural memory UI initialized")
        except Exception as e:
            logger.error(f"Failed to initialize procedural store: {e}")
            st.error(f"❌ Failed to initialize procedural memory: {e}")
    
    def render(self):
        """Render the main procedural memory interface."""
        if not self.store:
            st.error("❌ Procedural memory not available")
            return

        st.header("🧠 Procedural Memory")
        st.markdown("*Create, manage, and execute multi-step procedures and workflows*")

        # Phase 3: Enhanced interface with tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Procedures", "🚀 Execution Tracking", "💡 Suggestions", "📊 Analytics"])

        with tab1:
            # Statistics overview
            self._render_stats_overview()

            st.markdown("---")

            # Main two-panel layout
            col1, col2 = st.columns([1, 2])

            with col1:
                self._render_procedure_list()

            with col2:
                self._render_procedure_editor()

        with tab2:
            self._render_execution_tracking()

        with tab3:
            self._render_proactive_suggestions()

        with tab4:
            self._render_analytics_dashboard()
    
    def _render_stats_overview(self):
        """Render procedural memory statistics."""
        try:
            stats = self.store.get_procedure_stats()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Procedures", stats['total_procedures'])
            
            with col2:
                most_used = stats.get('most_used')
                if most_used:
                    st.metric("Most Used", most_used['name'], f"{most_used['execution_count']} times")
                else:
                    st.metric("Most Used", "None", "0 times")
            
            with col3:
                categories = stats.get('categories', {})
                st.metric("Categories", len(categories))
            
            with col4:
                recent_count = len(stats.get('recently_created', []))
                st.metric("Recent", f"{recent_count} this week")
            
        except Exception as e:
            logger.error(f"Failed to render stats: {e}")
            st.error("❌ Could not load statistics")
    
    def _render_procedure_list(self):
        """Render the procedure list panel."""
        st.subheader("📋 Procedures")
        
        # Search and filters
        search_query = st.text_input("🔍 Search procedures...", key="proc_search")
        
        # Filter options
        with st.expander("🎛️ Filters", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                categories = self._get_available_categories()
                selected_category = st.selectbox("Category", ["All"] + categories, key="proc_category_filter")
            
            with col2:
                difficulties = ["beginner", "intermediate", "advanced"]
                selected_difficulty = st.selectbox("Difficulty", ["All"] + difficulties, key="proc_difficulty_filter")
        
        # New procedure button
        if st.button("➕ New Procedure", use_container_width=True, type="primary"):
            st.session_state.selected_procedure_id = "new"
            st.session_state.procedure_editor_mode = "create"
            st.rerun()
        
        st.markdown("---")
        
        # Get and display procedures
        try:
            if search_query:
                # Perform search
                filters = {}
                if selected_category != "All":
                    filters['category'] = selected_category
                if selected_difficulty != "All":
                    filters['difficulty_level'] = selected_difficulty
                
                results = self.store.search_procedures(search_query, filters)
                procedures = [proc for proc, score in results]
            else:
                # Get all procedures with filtering
                procedures = self.store.get_all_procedures()
                
                # Apply filters
                if selected_category != "All":
                    procedures = [p for p in procedures if p.category == selected_category]
                if selected_difficulty != "All":
                    procedures = [p for p in procedures if p.difficulty_level == selected_difficulty]
            
            # Display procedures
            if not procedures:
                st.info("No procedures found. Create your first procedure!")
            else:
                for procedure in procedures:
                    self._render_procedure_item(procedure)
                    
        except Exception as e:
            logger.error(f"Failed to load procedures: {e}")
            st.error("❌ Could not load procedures")
    
    def _render_procedure_item(self, procedure):
        """Render a single procedure item in the list."""
        # Create a container for the procedure item
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Procedure name and description
                if st.button(
                    f"**{procedure.name}**",
                    key=f"select_proc_{procedure.id}",
                    help=procedure.description,
                    use_container_width=True
                ):
                    st.session_state.selected_procedure_id = procedure.id
                    st.session_state.procedure_editor_mode = "edit"
                    st.rerun()
                
                # Metadata
                col_meta1, col_meta2, col_meta3 = st.columns(3)
                with col_meta1:
                    if procedure.category:
                        st.caption(f"📂 {procedure.category}")
                with col_meta2:
                    st.caption(f"📊 {len(procedure.steps)} steps")
                with col_meta3:
                    st.caption(f"🔄 {procedure.execution_count} uses")
            
            with col2:
                # Quick actions
                if st.button("🗑️", key=f"delete_proc_{procedure.id}", help="Delete procedure"):
                    if st.session_state.get(f"confirm_delete_{procedure.id}", False):
                        # Perform deletion
                        success = self.store.delete_procedure(procedure.id)
                        if success:
                            st.success(f"Deleted: {procedure.name}")
                            st.rerun()
                        else:
                            st.error("Failed to delete procedure")
                    else:
                        # Ask for confirmation
                        st.session_state[f"confirm_delete_{procedure.id}"] = True
                        st.warning("Click again to confirm deletion")
                        st.rerun()
        
        st.markdown("---")
    
    def _render_procedure_editor(self):
        """Render the procedure editor panel."""
        if not st.session_state.get('selected_procedure_id'):
            st.info("👈 Select a procedure to edit, or create a new one")
            return
        
        procedure_id = st.session_state.selected_procedure_id
        mode = st.session_state.get('procedure_editor_mode', 'edit')
        
        if mode == "create" or procedure_id == "new":
            self._render_create_procedure_form()
        else:
            self._render_edit_procedure_form(procedure_id)
    
    def _render_create_procedure_form(self):
        """Render the form for creating a new procedure."""
        st.subheader("➕ Create New Procedure")
        
        with st.form("create_procedure_form"):
            # Basic information
            name = st.text_input("Procedure Name*", placeholder="e.g., Weekly Sales Report Workflow")
            description = st.text_area("Description*", placeholder="Brief description of what this procedure accomplishes")
            
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("Category", ["", "business", "personal", "technical", "other"])
            with col2:
                difficulty = st.selectbox("Difficulty", ["", "beginner", "intermediate", "advanced"])
            
            # Tags
            tags_input = st.text_input("Tags (comma-separated)", placeholder="reporting, sales, weekly")
            
            # Parameters
            st.subheader("Parameters (for reusable procedures)")
            parameters = self._render_parameters_editor({})
            
            # Steps
            st.subheader("Procedure Steps*")
            steps = self._render_steps_editor([])
            
            # Submit button
            submitted = st.form_submit_button("Create Procedure", type="primary")
            
            if submitted:
                if not name or not description or not steps:
                    st.error("Please fill in all required fields (marked with *)")
                else:
                    self._create_procedure(name, description, category, difficulty, tags_input, parameters, steps)
    
    def _render_edit_procedure_form(self, procedure_id: str):
        """Render the form for editing an existing procedure."""
        try:
            procedure = self.store.get_procedure(procedure_id)
            if not procedure:
                st.error("Procedure not found")
                return
            
            st.subheader(f"✏️ Edit: {procedure.name}")
            
            with st.form("edit_procedure_form"):
                # Basic information
                name = st.text_input("Procedure Name*", value=procedure.name)
                description = st.text_area("Description*", value=procedure.description)
                
                col1, col2 = st.columns(2)
                with col1:
                    categories = ["", "business", "personal", "technical", "other"]
                    current_category = procedure.category or ""
                    category_index = categories.index(current_category) if current_category in categories else 0
                    category = st.selectbox("Category", categories, index=category_index)
                
                with col2:
                    difficulties = ["", "beginner", "intermediate", "advanced"]
                    current_difficulty = procedure.difficulty_level or ""
                    difficulty_index = difficulties.index(current_difficulty) if current_difficulty in difficulties else 0
                    difficulty = st.selectbox("Difficulty", difficulties, index=difficulty_index)
                
                # Tags
                tags_str = ", ".join(procedure.tags)
                tags_input = st.text_input("Tags (comma-separated)", value=tags_str)
                
                # Parameters
                st.subheader("Parameters")
                parameters = self._render_parameters_editor(procedure.parameters)
                
                # Steps
                st.subheader("Procedure Steps*")
                steps_data = [
                    {
                        'description': step.description,
                        'details': step.details or '',
                        'expected_outcome': step.expected_outcome or ''
                    }
                    for step in procedure.steps
                ]
                steps = self._render_steps_editor(steps_data)
                
                # Submit button
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Update Procedure", type="primary")
                with col2:
                    if st.form_submit_button("Cancel", type="secondary"):
                        st.session_state.selected_procedure_id = None
                        st.rerun()
                
                if submitted:
                    if not name or not description or not steps:
                        st.error("Please fill in all required fields (marked with *)")
                    else:
                        self._update_procedure(procedure_id, name, description, category, difficulty, tags_input, parameters, steps)
                        
        except Exception as e:
            logger.error(f"Failed to render edit form: {e}")
            st.error("❌ Could not load procedure for editing")
    
    def _render_parameters_editor(self, current_parameters: Dict[str, str]) -> Dict[str, str]:
        """Render the parameters editor."""
        st.caption("Define reusable parameters like {email_recipient} or {file_path}")
        
        # Initialize session state for parameters
        if 'procedure_parameters' not in st.session_state:
            st.session_state.procedure_parameters = current_parameters.copy()
        
        parameters = st.session_state.procedure_parameters
        
        # Add new parameter
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            new_key = st.text_input("Parameter Name", key="new_param_key", placeholder="email_recipient")
        with col2:
            new_value = st.text_input("Default Value", key="new_param_value", placeholder="user@example.com")
        with col3:
            if st.button("➕", key="add_param", help="Add parameter"):
                if new_key and new_value:
                    parameters[new_key] = new_value
                    st.session_state.procedure_parameters = parameters
                    st.rerun()
        
        # Display existing parameters
        if parameters:
            for key, value in list(parameters.items()):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text_input("Key", value=key, disabled=True, key=f"param_key_{key}")
                with col2:
                    new_value = st.text_input("Value", value=value, key=f"param_value_{key}")
                    parameters[key] = new_value
                with col3:
                    if st.button("🗑️", key=f"delete_param_{key}", help="Delete parameter"):
                        del parameters[key]
                        st.session_state.procedure_parameters = parameters
                        st.rerun()
        
        return parameters
    
    def _render_steps_editor(self, current_steps: List[Dict]) -> List[Dict]:
        """Render the steps editor with dynamic management."""
        # Initialize session state for steps
        if 'procedure_steps' not in st.session_state:
            st.session_state.procedure_steps = current_steps.copy() if current_steps else []
        
        steps = st.session_state.procedure_steps
        
        # Add new step button
        if st.button("➕ Add Step", key="add_step"):
            steps.append({
                'description': '',
                'details': '',
                'expected_outcome': ''
            })
            st.session_state.procedure_steps = steps
            st.rerun()
        
        # Render existing steps
        if not steps:
            st.info("No steps added yet. Click 'Add Step' to begin.")
            return []
        
        for i, step in enumerate(steps):
            with st.expander(f"Step {i + 1}: {step.get('description', 'New Step')}", expanded=True):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Step fields
                    description = st.text_input(
                        "Description*",
                        value=step.get('description', ''),
                        key=f"step_desc_{i}",
                        placeholder="What needs to be done in this step?"
                    )
                    
                    details = st.text_area(
                        "Details",
                        value=step.get('details', ''),
                        key=f"step_details_{i}",
                        placeholder="Additional details, file paths, specific instructions..."
                    )
                    
                    expected_outcome = st.text_input(
                        "Expected Outcome",
                        value=step.get('expected_outcome', ''),
                        key=f"step_outcome_{i}",
                        placeholder="How to verify this step was completed successfully"
                    )
                    
                    # Update step data
                    steps[i] = {
                        'description': description,
                        'details': details,
                        'expected_outcome': expected_outcome
                    }
                
                with col2:
                    # Step controls
                    st.markdown("**Controls:**")
                    
                    # Move up
                    if i > 0 and st.button("⬆️", key=f"move_up_{i}", help="Move step up"):
                        steps[i], steps[i-1] = steps[i-1], steps[i]
                        st.session_state.procedure_steps = steps
                        st.rerun()
                    
                    # Move down
                    if i < len(steps) - 1 and st.button("⬇️", key=f"move_down_{i}", help="Move step down"):
                        steps[i], steps[i+1] = steps[i+1], steps[i]
                        st.session_state.procedure_steps = steps
                        st.rerun()
                    
                    # Delete step
                    if st.button("🗑️", key=f"delete_step_{i}", help="Delete step"):
                        steps.pop(i)
                        st.session_state.procedure_steps = steps
                        st.rerun()
        
        st.session_state.procedure_steps = steps
        return steps
    
    def _get_available_categories(self) -> List[str]:
        """Get list of available categories from existing procedures."""
        try:
            procedures = self.store.get_all_procedures()
            categories = set()
            for proc in procedures:
                if proc.category:
                    categories.add(proc.category)
            return sorted(list(categories))
        except:
            return ["business", "personal", "technical"]
    
    def _create_procedure(self, name: str, description: str, category: str, difficulty: str, 
                         tags_input: str, parameters: Dict[str, str], steps: List[Dict]):
        """Create a new procedure."""
        try:
            from sam.memory.procedural_memory import Procedure, ProcedureStep
            
            # Process tags
            tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            
            # Process steps
            procedure_steps = []
            for i, step_data in enumerate(steps):
                if step_data['description']:  # Only add steps with descriptions
                    procedure_steps.append(ProcedureStep(
                        step_number=i + 1,
                        description=step_data['description'],
                        details=step_data['details'] if step_data['details'] else None,
                        expected_outcome=step_data['expected_outcome'] if step_data['expected_outcome'] else None
                    ))
            
            # Create procedure
            procedure = Procedure(
                name=name,
                description=description,
                category=category if category else None,
                difficulty_level=difficulty if difficulty else None,
                tags=tags,
                parameters=parameters,
                steps=procedure_steps
            )
            
            # Save procedure
            success = self.store.add_procedure(procedure)
            
            if success:
                st.success(f"✅ Created procedure: {name}")
                # Clear form
                st.session_state.selected_procedure_id = None
                st.session_state.procedure_parameters = {}
                st.session_state.procedure_steps = []
                st.rerun()
            else:
                st.error("❌ Failed to create procedure")
                
        except Exception as e:
            logger.error(f"Failed to create procedure: {e}")
            st.error(f"❌ Error creating procedure: {e}")
    
    def _update_procedure(self, procedure_id: str, name: str, description: str, category: str, 
                         difficulty: str, tags_input: str, parameters: Dict[str, str], steps: List[Dict]):
        """Update an existing procedure."""
        try:
            from sam.memory.procedural_memory import ProcedureStep
            
            # Process tags
            tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            
            # Process steps
            procedure_steps = []
            for i, step_data in enumerate(steps):
                if step_data['description']:  # Only add steps with descriptions
                    procedure_steps.append(ProcedureStep(
                        step_number=i + 1,
                        description=step_data['description'],
                        details=step_data['details'] if step_data['details'] else None,
                        expected_outcome=step_data['expected_outcome'] if step_data['expected_outcome'] else None
                    ))
            
            # Update data
            update_data = {
                'name': name,
                'description': description,
                'category': category if category else None,
                'difficulty_level': difficulty if difficulty else None,
                'tags': tags,
                'parameters': parameters,
                'steps': procedure_steps
            }
            
            # Save changes
            success = self.store.update_procedure(procedure_id, update_data)
            
            if success:
                st.success(f"✅ Updated procedure: {name}")
                # Clear form state
                st.session_state.procedure_parameters = {}
                st.session_state.procedure_steps = []
                st.rerun()
            else:
                st.error("❌ Failed to update procedure")
                
        except Exception as e:
            logger.error(f"Failed to update procedure: {e}")
            st.error(f"❌ Error updating procedure: {e}")

    def _render_execution_tracking(self):
        """Render the execution tracking interface."""
        st.subheader("🚀 Execution Tracking")
        st.markdown("*Monitor and track procedure execution progress*")

        try:
            from sam.memory.execution_tracker import get_execution_tracker
            tracker = get_execution_tracker()

            # Active executions
            active_executions = tracker.get_user_active_executions()

            if active_executions:
                st.markdown("### 🔄 Active Executions")

                for execution in active_executions:
                    with st.expander(f"📋 {execution.procedure_name}", expanded=True):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Status", execution.status.value.title())
                        with col2:
                            st.metric("Current Step", f"{execution.current_step}")
                        with col3:
                            duration = (datetime.now() - execution.started_at).total_seconds() / 60
                            st.metric("Duration", f"{duration:.1f} min")

                        # Step progress
                        if execution.steps:
                            st.markdown("**Step Progress:**")
                            for step_num, step in execution.steps.items():
                                status_icon = {
                                    'pending': '⏳',
                                    'in_progress': '🔄',
                                    'completed': '✅',
                                    'failed': '❌',
                                    'skipped': '⏭️'
                                }.get(step.status.value, '❓')

                                st.markdown(f"{status_icon} Step {step_num}: {step.status.value.title()}")

                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("⏸️ Pause", key=f"pause_{execution.execution_id}"):
                                tracker.pause_execution(execution.execution_id)
                                st.rerun()
                        with col2:
                            if st.button("✅ Complete", key=f"complete_{execution.execution_id}"):
                                tracker.complete_execution(execution.execution_id)
                                st.success("Execution completed!")
                                st.rerun()
                        with col3:
                            if st.button("❌ Cancel", key=f"cancel_{execution.execution_id}"):
                                # Implementation for canceling execution
                                st.warning("Execution cancelled")
            else:
                st.info("No active executions. Start a procedure to begin tracking.")

            # Quick start execution
            st.markdown("---")
            st.markdown("### ▶️ Start New Execution")

            procedures = self.store.get_all_procedures()
            if procedures:
                procedure_options = {proc.name: proc.id for proc in procedures}
                selected_procedure = st.selectbox("Select Procedure", list(procedure_options.keys()))

                if st.button("🚀 Start Execution", type="primary"):
                    procedure_id = procedure_options[selected_procedure]
                    execution_id = tracker.start_execution(
                        procedure_id=procedure_id,
                        procedure_name=selected_procedure,
                        user_id="default"
                    )
                    if execution_id:
                        st.success(f"Started execution: {execution_id}")
                        st.rerun()
                    else:
                        st.error("Failed to start execution")
            else:
                st.info("Create procedures first to enable execution tracking.")

        except Exception as e:
            st.error(f"❌ Execution tracking not available: {e}")

    def _render_proactive_suggestions(self):
        """Render the proactive suggestions interface."""
        st.subheader("💡 Proactive Suggestions")
        st.markdown("*AI-powered suggestions based on your workflow patterns*")

        try:
            from sam.cognition.proactive_suggestions import get_proactive_suggestion_engine
            suggestion_engine = get_proactive_suggestion_engine()

            # Get active suggestions
            suggestions = suggestion_engine.get_active_suggestions()

            if suggestions:
                st.markdown("### 🎯 Recommended Actions")

                for suggestion in suggestions:
                    with st.container():
                        # Priority indicator
                        priority_colors = {1: "🔵", 2: "🟢", 3: "🟡", 4: "🟠", 5: "🔴"}
                        priority_icon = priority_colors.get(suggestion.priority, "⚪")

                        st.markdown(f"#### {priority_icon} {suggestion.title}")
                        st.markdown(f"**Type:** {suggestion.type.replace('_', ' ').title()}")
                        st.markdown(f"**Description:** {suggestion.description}")
                        st.markdown(f"**Rationale:** {suggestion.rationale}")
                        st.markdown(f"**Potential Benefit:** {suggestion.potential_benefit}")

                        # Confidence bar
                        st.progress(suggestion.confidence, text=f"Confidence: {suggestion.confidence:.0%}")

                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("✅ Accept", key=f"accept_{suggestion.suggestion_id}"):
                                suggestion_engine.accept_suggestion(suggestion.suggestion_id)
                                st.success("Suggestion accepted!")
                                st.rerun()
                        with col2:
                            if st.button("❌ Dismiss", key=f"dismiss_{suggestion.suggestion_id}"):
                                suggestion_engine.dismiss_suggestion(suggestion.suggestion_id)
                                st.info("Suggestion dismissed")
                                st.rerun()
                        with col3:
                            if st.button("ℹ️ More Info", key=f"info_{suggestion.suggestion_id}"):
                                with st.expander("Suggested Actions", expanded=True):
                                    for action in suggestion.suggested_actions:
                                        st.markdown(f"• {action}")

                        st.markdown("---")
            else:
                st.info("No suggestions available yet. Keep using SAM to build your workflow patterns!")

            # Analytics summary
            analytics = suggestion_engine.get_suggestion_analytics()
            if analytics:
                st.markdown("### 📈 Pattern Analysis")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("User Actions", analytics.get('total_user_actions', 0))
                with col2:
                    st.metric("Patterns Detected", analytics.get('detected_patterns', 0))
                with col3:
                    st.metric("Active Suggestions", analytics.get('active_suggestions', 0))
                with col4:
                    avg_confidence = analytics.get('average_pattern_confidence', 0)
                    st.metric("Avg Confidence", f"{avg_confidence:.0%}")

        except Exception as e:
            st.error(f"❌ Proactive suggestions not available: {e}")

    def _render_analytics_dashboard(self):
        """Render the analytics dashboard."""
        st.subheader("📊 Analytics Dashboard")
        st.markdown("*Insights and performance metrics for your procedures*")

        try:
            # Procedure analytics
            stats = self.store.get_procedure_stats()

            st.markdown("### 📋 Procedure Overview")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Procedures", stats.get('total_procedures', 0))
            with col2:
                categories = stats.get('categories', {})
                st.metric("Categories", len(categories))
            with col3:
                most_used = stats.get('most_used')
                if most_used:
                    st.metric("Most Used", most_used['execution_count'])
                else:
                    st.metric("Most Used", 0)
            with col4:
                recent = stats.get('recently_created', [])
                st.metric("Recent (Week)", len(recent))

            # Category distribution
            if categories:
                st.markdown("### 📂 Category Distribution")
                category_data = list(categories.items())
                category_names = [item[0] for item in category_data]
                category_counts = [item[1] for item in category_data]

                # Simple bar chart using Streamlit
                chart_data = dict(zip(category_names, category_counts))
                st.bar_chart(chart_data)

            # Execution analytics
            try:
                from sam.memory.execution_tracker import get_execution_tracker
                tracker = get_execution_tracker()

                st.markdown("### 🚀 Execution Analytics")

                # Get analytics for all procedures
                exec_analytics = tracker.get_execution_analytics()

                if exec_analytics.get('total_executions', 0) > 0:
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Total Executions", exec_analytics['total_executions'])
                    with col2:
                        success_rate = exec_analytics.get('success_rate', 0)
                        st.metric("Success Rate", f"{success_rate:.0%}")
                    with col3:
                        avg_duration = exec_analytics.get('average_duration_minutes', 0)
                        st.metric("Avg Duration", f"{avg_duration:.1f} min")
                    with col4:
                        avg_rating = exec_analytics.get('average_success_rating', 0)
                        st.metric("Avg Rating", f"{avg_rating:.1f}/5")

                    # Common issues
                    common_issues = exec_analytics.get('common_issues', [])
                    if common_issues:
                        st.markdown("### ⚠️ Common Issues")
                        for issue, count in common_issues[:5]:
                            st.markdown(f"• **{issue}** ({count} occurrences)")
                else:
                    st.info("No execution data available yet. Start executing procedures to see analytics.")

            except Exception as e:
                st.warning(f"Execution analytics not available: {e}")

            # Proactive suggestions analytics
            try:
                from sam.cognition.proactive_suggestions import get_proactive_suggestion_engine
                suggestion_engine = get_proactive_suggestion_engine()

                suggestion_analytics = suggestion_engine.get_suggestion_analytics()

                if suggestion_analytics:
                    st.markdown("### 🧠 Intelligence Analytics")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Behavior Patterns", suggestion_analytics.get('detected_patterns', 0))
                    with col2:
                        st.metric("Active Suggestions", suggestion_analytics.get('active_suggestions', 0))
                    with col3:
                        st.metric("User Actions", suggestion_analytics.get('total_user_actions', 0))

                    # Action type distribution
                    action_dist = suggestion_analytics.get('action_type_distribution', {})
                    if action_dist:
                        st.markdown("**Action Type Distribution:**")
                        for action_type, count in action_dist.items():
                            st.markdown(f"• {action_type.replace('_', ' ').title()}: {count}")

            except Exception as e:
                st.warning(f"Intelligence analytics not available: {e}")

        except Exception as e:
            st.error(f"❌ Analytics dashboard not available: {e}")

def render_procedural_memory_ui():
    """Main function to render the procedural memory UI."""
    ui = ProceduralMemoryUI()
    ui.render()
