#!/usr/bin/env python3
"""
Project Cleanup Script - Remove unnecessary files while preserving important data
"""

import os
import shutil
from datetime import datetime

def cleanup_project():
    """Clean up project folder while preserving important data."""
    
    print("🧹 PROJECT CLEANUP - PRESERVING IMPORTANT DATA")
    print("=" * 60)
    
    # CRITICAL FILES TO PRESERVE (NEVER DELETE)
    preserve_files = {
        # FINAL OUTPUT (MOST IMPORTANT)
        'FINAL_METABASE_REPORTS_WITH_BUSINESS_CONTEXT_20250801_162929.xlsx',
        
        # ORIGINAL DATA SOURCES
        'metabase_reports_detailed_20250731_122354.xlsx',
        'metabase_reports_analysis.xlsx',
        
        # CONFIGURATION
        'gemini_config.env',
        'metabase_config.env',
        'requirements.txt',
        
        # DOCUMENTATION
        'README.md',
        'METABASE_SETUP_GUIDE.md',
        'GEMINI_PROCESSING_README.md',
        
        # CORE PROCESSING SCRIPTS (KEEP FOR FUTURE USE)
        'gemini_business_context_generator.py',
        'large_batch_processor.py',
        'metabase_api_fetcher.py',
    }
    
    # FILES TO DELETE (TEMPORARY/TEST/DUPLICATE)
    delete_files = []
    
    # Get all files in current directory
    all_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    
    print("📋 CATEGORIZING FILES...")
    
    # Temporary progress files (all the temp_progress_*.xlsx files)
    temp_progress_files = [f for f in all_files if f.startswith('temp_progress_') and f.endswith('.xlsx')]
    delete_files.extend(temp_progress_files)
    print(f"🗑️ Found {len(temp_progress_files)} temporary progress files")
    
    # Old result files (keep only the final one)
    old_result_files = [f for f in all_files if 
                       ('metabase_reports_with_business_context' in f and 
                        f != 'FINAL_METABASE_REPORTS_WITH_BUSINESS_CONTEXT_20250801_162929.xlsx')]
    delete_files.extend(old_result_files)
    print(f"🗑️ Found {len(old_result_files)} old result files")
    
    # Test and migration scripts (temporary)
    test_migration_files = [
        'test_bulletproof_3_reports.py',
        'test_save_mechanism.py',
        'migrate_existing_results.py',
        'bulletproof_recovery.py',
        'process_missing_reports.py',
        'combine_all_results.py',
        'resume_processing.py',
        'create_final_mapped_results.py',
        'cleanup_project.py'  # This script itself
    ]
    for f in test_migration_files:
        if f in all_files:
            delete_files.append(f)
    print(f"🗑️ Found {len([f for f in test_migration_files if f in all_files])} test/migration scripts")
    
    # Alternative/backup processor files
    alt_processors = [
        'bulletproof_gemini_processor.py',
        'small_batch_processor.py',
        'gemini_business_context_generator_optimized.py'
    ]
    for f in alt_processors:
        if f in all_files:
            delete_files.append(f)
    print(f"🗑️ Found {len([f for f in alt_processors if f in all_files])} alternative processor files")
    
    # Old/duplicate Excel files
    old_excel_files = [
        'COMPLETE_metabase_reports_with_business_context_20250801_004755.xlsx',
        'MASTER_BULLETPROOF_RESULTS.xlsx',  # Replaced by final file
        'ai_summary_assessment_results.xlsx',
        'metabase_reports_detailed_20250731_120550.xlsx',
        'my_metabase_reports_20250731_123642.xlsx'
    ]
    for f in old_excel_files:
        if f in all_files:
            delete_files.append(f)
    print(f"🗑️ Found {len([f for f in old_excel_files if f in all_files])} old Excel files")
    
    # Assessment and comparison files (completed work)
    assessment_files = [
        'AI_Summary_Quality_Assessment_Report.md',
        'Gemini_Model_Comparison_Report.md',
        'CRITICAL_DESIGN_FIXES.md',
        'ai_summary_quality_assessment.py',
        'generate_markdown_report.py',
        'read_excel.py'
    ]
    for f in assessment_files:
        if f in all_files:
            delete_files.append(f)
    print(f"🗑️ Found {len([f for f in assessment_files if f in all_files])} assessment files")
    
    # Setup scripts (no longer needed)
    setup_files = [
        'setup_gemini_api_key.py',
        'setup_metabase_config.py',
        'fetch_my_reports.py',
        'fetch_specific_reports.py'
    ]
    for f in setup_files:
        if f in all_files:
            delete_files.append(f)
    print(f"🗑️ Found {len([f for f in setup_files if f in all_files])} setup scripts")
    
    # State and log files
    state_log_files = [
        'BULLETPROOF_STATE.json',
        'gemini_business_context.log',
        'large_batch_processor.log',
        'bulletproof_processor.log',
        'metabase_api_fetcher.log'
    ]
    for f in state_log_files:
        if f in all_files:
            delete_files.append(f)
    print(f"🗑️ Found {len([f for f in state_log_files if f in all_files])} state/log files")
    
    # Remove duplicates and ensure we don't delete preserved files
    delete_files = list(set(delete_files))
    delete_files = [f for f in delete_files if f not in preserve_files]
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"   • Total files: {len(all_files)}")
    print(f"   • Files to preserve: {len(preserve_files)}")
    print(f"   • Files to delete: {len(delete_files)}")
    
    # Show what will be preserved
    print(f"\n✅ FILES TO PRESERVE:")
    preserved_found = [f for f in preserve_files if f in all_files]
    for f in sorted(preserved_found):
        print(f"   📁 {f}")
    
    # Show what will be deleted
    print(f"\n🗑️ FILES TO DELETE:")
    for f in sorted(delete_files):
        print(f"   ❌ {f}")
    
    # Ask for confirmation
    print(f"\n⚠️ CONFIRMATION REQUIRED:")
    print(f"This will delete {len(delete_files)} files and preserve {len(preserved_found)} important files.")
    response = input("Proceed with cleanup? (y/n): ").lower()
    
    if response != 'y':
        print("❌ Cleanup cancelled by user")
        return
    
    # Perform cleanup
    print(f"\n🧹 PERFORMING CLEANUP...")
    deleted_count = 0
    error_count = 0
    
    for file_to_delete in delete_files:
        try:
            if os.path.exists(file_to_delete):
                os.remove(file_to_delete)
                print(f"✅ Deleted: {file_to_delete}")
                deleted_count += 1
        except Exception as e:
            print(f"❌ Error deleting {file_to_delete}: {e}")
            error_count += 1
    
    # Clean up directories
    dirs_to_clean = ['__pycache__', 'EMERGENCY_BACKUPS']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✅ Deleted directory: {dir_name}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Error deleting directory {dir_name}: {e}")
                error_count += 1
    
    print(f"\n🎉 CLEANUP COMPLETED!")
    print(f"   • Files deleted: {deleted_count}")
    print(f"   • Errors: {error_count}")
    print(f"   • Files preserved: {len(preserved_found)}")
    
    print(f"\n📁 YOUR CLEAN PROJECT NOW CONTAINS:")
    remaining_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for f in sorted(remaining_files):
        size = os.path.getsize(f) / 1024  # KB
        print(f"   📄 {f} ({size:.1f}KB)")
    
    print(f"\n✨ PROJECT CLEANED SUCCESSFULLY!")
    print(f"🎯 Your final output file: FINAL_METABASE_REPORTS_WITH_BUSINESS_CONTEXT_20250801_162929.xlsx")

if __name__ == "__main__":
    cleanup_project() 