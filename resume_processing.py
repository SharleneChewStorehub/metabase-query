#!/usr/bin/env python3
"""
Resume Processing Script

This script automatically detects where the previous processing stopped
and resumes from the correct report number.
"""

import re
import os
from gemini_business_context_generator import GeminiBusinessContextGenerator

def find_last_processed_report():
    """Find the last successfully processed report from the log file."""
    if not os.path.exists('gemini_business_context.log'):
        print("❌ No log file found. Starting from Report_1")
        return 1
    
    try:
        with open('gemini_business_context.log', 'r') as f:
            lines = f.readlines()
        
        # Look for the last successfully processed report
        last_completed = 0
        for line in reversed(lines):
            if "Successfully generated business context" in line:
                # Extract report number from line like: "✅ Report_798: Successfully generated business context"
                match = re.search(r'Report_(\d+):', line)
                if match:
                    last_completed = int(match.group(1))
                    break
        
        if last_completed > 0:
            resume_from = last_completed + 1
            print(f"📊 Last completed: Report_{last_completed}")
            print(f"🔄 Will resume from: Report_{resume_from}")
            return resume_from
        else:
            print("❌ No completed reports found in log. Starting from Report_1")
            return 1
            
    except Exception as e:
        print(f"❌ Error reading log file: {e}")
        print("Starting from Report_1")
        return 1

def main():
    """Resume processing from where it left off."""
    print("🔄 RESUME PROCESSING SCRIPT")
    print("=" * 50)
    
    # Find where to resume from
    resume_from_report = find_last_processed_report()
    
    # Configuration
    excel_file = "metabase_reports_detailed_20250731_122354.xlsx"
    
    try:
        # Initialize generator
        print(f"\n🔧 Initializing generator...")
        generator = GeminiBusinessContextGenerator(excel_file)
        
        # Setup Gemini API
        print("🔑 Setting up Gemini API...")
        if not generator.setup_gemini_api():
            print("\n❌ API setup failed. Please configure your Gemini API key.")
            return
        
        # Load Excel data
        print("📖 Loading Excel data...")
        if not generator.load_excel_data():
            print("❌ Failed to load Excel data.")
            return
        
        # Show resume information
        total_reports = len(generator.df)
        already_completed = resume_from_report - 1
        remaining = total_reports - already_completed
        
        print(f"\n🎯 Resume Summary:")
        print(f"   • Total reports: {total_reports}")
        print(f"   • Already completed: {already_completed}")
        print(f"   • Remaining to process: {remaining}")
        print(f"   • Resuming from: Report_{resume_from_report}")
        print(f"   • Progress: {(already_completed/total_reports)*100:.1f}% complete")
        
        # Process reports
        if generator.process_reports(start_from_report=resume_from_report):
            # Save final results
            print("\n💾 Saving final results...")
            output_file = generator.save_results()
            
            # Display summary
            generator.display_summary()
            
            if output_file:
                print(f"\n📋 Final results saved to: {output_file}")
        
        print("\n✨ Processing complete!")
        
    except KeyboardInterrupt:
        print("\n🛑 Processing interrupted by user")
        print("Your progress has been saved. Run this script again to resume.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")

if __name__ == "__main__":
    main() 