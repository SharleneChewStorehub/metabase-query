#!/usr/bin/env python3
"""
Verification script for 400 Recent Active Reports processing setup.
Checks all requirements and configurations before running the main process.
"""

import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

def verify_setup():
    """Verify all requirements for processing 400 recent active reports."""
    print("🔍 VERIFICATION - Recent 400 Reports Processing Setup")
    print("=" * 60)
    
    checks_passed = 0
    total_checks = 7
    
    # 1. Check input file exists
    print("1. Checking input file...")
    input_file = "COMPLETE_recent_metabase_reports_20250803_035047.xlsx"
    if os.path.exists(input_file):
        df = pd.read_excel(input_file)
        print(f"   ✅ Input file found: {len(df)} reports")
        checks_passed += 1
        
        # Check required columns
        required_cols = ['report_id', 'report_name', 'sql_query']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if not missing_cols:
            print(f"   ✅ All required columns present")
        else:
            print(f"   ❌ Missing columns: {missing_cols}")
    else:
        print(f"   ❌ Input file not found: {input_file}")
    
    # 2. Check Gemini API configuration
    print("\n2. Checking Gemini API configuration...")
    gemini_config_files = ['gemini_config.env', '.env']
    gemini_configured = False
    
    for config_file in gemini_config_files:
        if os.path.exists(config_file):
            load_dotenv(config_file)
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key and api_key != 'your-api-key-here':
                print(f"   ✅ Gemini API key found in {config_file}")
                gemini_configured = True
                checks_passed += 1
                break
    
    if not gemini_configured:
        print(f"   ❌ Gemini API key not configured")
        print(f"   📝 Run: python3 setup_gemini_api_key.py")
    
    # 3. Check Gemini generator exists
    print("\n3. Checking Gemini generator...")
    if os.path.exists('gemini_business_context_generator.py'):
        print(f"   ✅ Gemini generator found")
        checks_passed += 1
    else:
        print(f"   ❌ Gemini generator not found")
    
    # 4. Check Python dependencies
    print("\n4. Checking Python dependencies...")
    try:
        import google.generativeai as genai
        import pandas
        import openpyxl
        print(f"   ✅ All required packages installed")
        checks_passed += 1
    except ImportError as e:
        print(f"   ❌ Missing dependency: {e}")
        print(f"   📝 Run: pip install -r requirements.txt")
    
    # 5. Check write permissions
    print("\n5. Checking write permissions...")
    try:
        test_file = "test_write_permission.tmp"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print(f"   ✅ Write permissions OK")
        checks_passed += 1
    except Exception as e:
        print(f"   ❌ Write permission error: {e}")
    
    # 6. Check previous 1550 results (for reference)
    print("\n6. Checking previous processing results...")
    prev_files = [
        'FINAL_METABASE_REPORTS_WITH_BUSINESS_CONTEXT_20250801.xlsx',
        'FINAL_METABASE_REPORTS_WITH_USAGE_CONTEXT_20250803_145510.xlsx'
    ]
    
    prev_found = 0
    for file in prev_files:
        if os.path.exists(file):
            prev_found += 1
    
    if prev_found > 0:
        print(f"   ✅ Previous processing results found ({prev_found} files)")
        checks_passed += 1
    else:
        print(f"   ⚠️  Previous results not found (OK for fresh start)")
        checks_passed += 1  # Not critical
    
    # 7. Check available disk space (estimate)
    print("\n7. Checking available resources...")
    try:
        import shutil
        free_space = shutil.disk_usage('.').free
        required_space = 100 * 1024 * 1024  # 100MB estimate
        
        if free_space > required_space:
            print(f"   ✅ Sufficient disk space available")
            checks_passed += 1
        else:
            print(f"   ❌ Low disk space: {free_space // (1024*1024)}MB free")
    except Exception:
        print(f"   ⚠️  Could not check disk space")
        checks_passed += 1  # Not critical
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 VERIFICATION SUMMARY: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("🎉 ALL CHECKS PASSED - Ready to process 400 reports!")
        print("\n🚀 To start processing, run:")
        print("   python3 process_recent_400_reports.py")
        
        # Show expected processing time
        print(f"\n⏱️  Expected processing time:")
        print(f"   • 400 reports × 1.5s delay = ~10 minutes for API calls")
        print(f"   • Plus AI processing time = ~15-20 minutes total")
        print(f"   • Auto-save every 10 reports")
        print(f"   • Can resume if interrupted")
        
        return True
    else:
        failed_checks = total_checks - checks_passed
        print(f"❌ {failed_checks} CHECKS FAILED - Please fix issues before proceeding")
        
        if not gemini_configured:
            print(f"\n🔧 CRITICAL: Set up Gemini API key first:")
            print(f"   python3 setup_gemini_api_key.py")
        
        return False

def show_expected_output():
    """Show what the output will look like."""
    print("\n📁 EXPECTED OUTPUT FILES:")
    print("   • RECENT_400_REPORTS_WITH_BUSINESS_CONTEXT.xlsx")
    print("     └── Business_Context_Results (main results)")
    print("     └── Processing_Summary (statistics)")
    print("     └── Failed_Reports (if any failures)")
    print("   • recent_400_processor.log (detailed logs)")
    print("   • EMERGENCY_BACKUPS_400/ (automatic backups)")
    print("   • RECENT_400_STATE.json (recovery state)")

if __name__ == "__main__":
    success = verify_setup()
    show_expected_output()
    
    if success:
        print(f"\n✅ System ready for processing!")
    else:
        print(f"\n❌ Please resolve issues before proceeding.") 