#!/usr/bin/env python3
"""
Sample Procedures for SAM Procedural Memory
===========================================

This script creates sample procedures to demonstrate the Procedural Memory Engine
capabilities and provide examples for users.

Author: SAM Development Team
Version: 2.0.0
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_sample_procedures():
    """Create sample procedures to demonstrate the system."""
    print("🧠 Creating Sample Procedures for Procedural Memory...")
    
    try:
        from sam.memory.procedural_memory import get_procedural_memory_store, Procedure, ProcedureStep
        
        store = get_procedural_memory_store()
        
        # Sample Procedure 1: Weekly Sales Report
        sales_report_steps = [
            ProcedureStep(
                step_number=1,
                description="Open the weekly sales report spreadsheet",
                details="Navigate to {report_path} and open the Excel file",
                expected_outcome="The sales report spreadsheet is open and visible",
                estimated_duration="2 minutes",
                tools_required=["Excel", "Network access"]
            ),
            ProcedureStep(
                step_number=2,
                description="Refresh all data connections",
                details="Go to Data tab → Refresh All to update with latest data",
                expected_outcome="All charts and tables show current week's data",
                estimated_duration="3 minutes"
            ),
            ProcedureStep(
                step_number=3,
                description="Review and validate the numbers",
                details="Check for any anomalies or unexpected changes in sales figures",
                expected_outcome="Data appears accurate and consistent",
                estimated_duration="5 minutes"
            ),
            ProcedureStep(
                step_number=4,
                description="Export summary chart",
                details="Copy the main summary chart and paste as image",
                expected_outcome="Chart is copied to clipboard as image",
                estimated_duration="1 minute"
            ),
            ProcedureStep(
                step_number=5,
                description="Send email to sales team",
                details="Create new email to {email_recipient} with chart and brief summary",
                expected_outcome="Email sent successfully to sales team",
                estimated_duration="5 minutes"
            )
        ]
        
        sales_report_procedure = Procedure(
            name="Weekly Sales Report Workflow",
            description="Complete workflow for generating and distributing the weekly sales report to the team",
            tags=["reporting", "sales", "weekly", "business"],
            category="business",
            difficulty_level="intermediate",
            estimated_total_time="15-20 minutes",
            parameters={
                "report_path": "/reports/weekly_sales.xlsx",
                "email_recipient": "sales-team@company.com"
            },
            steps=sales_report_steps
        )
        
        # Sample Procedure 2: System Backup
        backup_steps = [
            ProcedureStep(
                step_number=1,
                description="Check available disk space",
                details="Ensure backup destination has at least 50GB free space",
                expected_outcome="Sufficient space confirmed for backup",
                estimated_duration="1 minute",
                prerequisites=["Admin access", "Backup destination mounted"]
            ),
            ProcedureStep(
                step_number=2,
                description="Stop non-essential services",
                details="Stop services that might interfere with backup: web server, app server",
                expected_outcome="Services stopped successfully",
                estimated_duration="2 minutes"
            ),
            ProcedureStep(
                step_number=3,
                description="Run database backup",
                details="Execute: mysqldump -u {db_user} -p {db_name} > backup_{date}.sql",
                expected_outcome="Database backup file created successfully",
                estimated_duration="10 minutes"
            ),
            ProcedureStep(
                step_number=4,
                description="Backup application files",
                details="Create tar archive of application directory: tar -czf app_backup_{date}.tar.gz /var/www/app",
                expected_outcome="Application files archived successfully",
                estimated_duration="5 minutes"
            ),
            ProcedureStep(
                step_number=5,
                description="Verify backup integrity",
                details="Check file sizes and run test restore on sample data",
                expected_outcome="Backup files are valid and restorable",
                estimated_duration="3 minutes"
            ),
            ProcedureStep(
                step_number=6,
                description="Restart services",
                details="Start all services that were stopped in step 2",
                expected_outcome="All services running normally",
                estimated_duration="2 minutes"
            )
        ]
        
        backup_procedure = Procedure(
            name="System Backup Procedure",
            description="Complete system backup including database and application files with verification",
            tags=["backup", "system", "database", "maintenance"],
            category="technical",
            difficulty_level="advanced",
            estimated_total_time="25-30 minutes",
            parameters={
                "db_user": "backup_user",
                "db_name": "production_db",
                "date": "$(date +%Y%m%d)"
            },
            steps=backup_steps
        )
        
        # Sample Procedure 3: Team Meeting Setup
        meeting_steps = [
            ProcedureStep(
                step_number=1,
                description="Schedule meeting in calendar",
                details="Create recurring weekly meeting for {meeting_time} with team members",
                expected_outcome="Meeting appears in everyone's calendar",
                estimated_duration="3 minutes"
            ),
            ProcedureStep(
                step_number=2,
                description="Prepare agenda template",
                details="Use standard agenda: Updates, Blockers, Goals, Action Items",
                expected_outcome="Agenda document ready for meeting",
                estimated_duration="5 minutes"
            ),
            ProcedureStep(
                step_number=3,
                description="Set up meeting room",
                details="Book conference room, test AV equipment, prepare whiteboard",
                expected_outcome="Meeting room ready for team",
                estimated_duration="5 minutes"
            ),
            ProcedureStep(
                step_number=4,
                description="Send reminder with agenda",
                details="Email team 24 hours before with agenda and any prep materials",
                expected_outcome="Team receives reminder and agenda",
                estimated_duration="2 minutes"
            )
        ]
        
        meeting_procedure = Procedure(
            name="Weekly Team Meeting Setup",
            description="Standard process for organizing and preparing weekly team meetings",
            tags=["meeting", "team", "weekly", "organization"],
            category="business",
            difficulty_level="beginner",
            estimated_total_time="15 minutes",
            parameters={
                "meeting_time": "Fridays 2:00 PM",
                "team_size": "6 people"
            },
            steps=meeting_steps
        )
        
        # Sample Procedure 4: Code Deployment
        deployment_steps = [
            ProcedureStep(
                step_number=1,
                description="Run all tests",
                details="Execute full test suite: npm test && npm run test:integration",
                expected_outcome="All tests pass with no failures",
                estimated_duration="5 minutes",
                prerequisites=["Code reviewed", "Tests written"]
            ),
            ProcedureStep(
                step_number=2,
                description="Build production version",
                details="Create optimized build: npm run build:production",
                expected_outcome="Build completes without errors",
                estimated_duration="3 minutes"
            ),
            ProcedureStep(
                step_number=3,
                description="Deploy to staging",
                details="Deploy to staging environment for final testing",
                expected_outcome="Application running on staging server",
                estimated_duration="2 minutes"
            ),
            ProcedureStep(
                step_number=4,
                description="Smoke test on staging",
                details="Test critical user flows and API endpoints",
                expected_outcome="All critical functionality working",
                estimated_duration="10 minutes"
            ),
            ProcedureStep(
                step_number=5,
                description="Deploy to production",
                details="Deploy to production servers using blue-green deployment",
                expected_outcome="New version live on production",
                estimated_duration="5 minutes"
            ),
            ProcedureStep(
                step_number=6,
                description="Monitor deployment",
                details="Watch logs and metrics for 15 minutes post-deployment",
                expected_outcome="No errors or performance issues detected",
                estimated_duration="15 minutes"
            )
        ]
        
        deployment_procedure = Procedure(
            name="Code Deployment Process",
            description="Safe deployment process for web applications with testing and monitoring",
            tags=["deployment", "code", "production", "testing"],
            category="technical",
            difficulty_level="intermediate",
            estimated_total_time="40 minutes",
            parameters={
                "environment": "production",
                "app_name": "web-app"
            },
            steps=deployment_steps
        )
        
        # Add all procedures to store
        procedures = [
            sales_report_procedure,
            backup_procedure,
            meeting_procedure,
            deployment_procedure
        ]
        
        created_count = 0
        for procedure in procedures:
            success = store.add_procedure(procedure)
            if success:
                created_count += 1
                print(f"✅ Created: {procedure.name}")
            else:
                print(f"❌ Failed to create: {procedure.name}")
        
        print(f"\n🎉 Successfully created {created_count}/{len(procedures)} sample procedures!")
        print("\n📋 Sample Procedures Created:")
        print("1. Weekly Sales Report Workflow (Business, Intermediate)")
        print("2. System Backup Procedure (Technical, Advanced)")
        print("3. Weekly Team Meeting Setup (Business, Beginner)")
        print("4. Code Deployment Process (Technical, Intermediate)")
        
        print("\n🚀 You can now:")
        print("• View procedures in Memory Control Center → 🧠 Procedures")
        print("• Search for procedures: 'how do I backup the system?'")
        print("• Edit and customize procedures for your needs")
        print("• Create new procedures based on these examples")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample procedures: {e}")
        return False

def main():
    """Main function to create sample procedures."""
    print("🧠 SAM Procedural Memory - Sample Procedures Creator")
    print("=" * 60)
    
    success = create_sample_procedures()
    
    if success:
        print("\n✅ Sample procedures created successfully!")
        print("🎯 Ready to explore Procedural Memory features")
    else:
        print("\n❌ Failed to create sample procedures")
        print("🔧 Please check the error messages above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
