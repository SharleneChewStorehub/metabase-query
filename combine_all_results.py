#!/usr/bin/env python3
"""
Combine All Results Script

This script combines all incremental progress files and the final results
to create one complete Excel file with all processed reports.
"""

import pandas as pd
import os
import glob
from datetime import datetime

def combine_all_results():
    """Combine all progress files and final results into one complete file."""
    
    print("🔄 COMBINING ALL RESULTS")
    print("=" * 50)
    
    all_results = []
    all_failed = []
    processed_report_ids = set()
    
    # Get all progress files and the final file
    progress_files = glob.glob("temp_progress_*.xlsx")
    final_files = glob.glob("metabase_reports_with_business_context_*.xlsx")
    
    all_files = progress_files + final_files
    all_files.sort(key=lambda x: os.path.getmtime(x))  # Sort by modification time
    
    print(f"📋 Found {len(all_files)} files to process:")
    for f in all_files:
        size_kb = os.path.getsize(f) / 1024
        print(f"   • {f} ({size_kb:.1f} KB)")
    
    print(f"\n🔄 Processing files...")
    
    for file_path in all_files:
        try:
            print(f"📖 Reading: {file_path}")
            
            # Read the Business_Context_Results sheet
            try:
                df_results = pd.read_excel(file_path, sheet_name='Business_Context_Results')
                print(f"   ✅ Found {len(df_results)} results")
                
                # Add only new results (avoid duplicates)
                new_results = 0
                for _, row in df_results.iterrows():
                    report_id = row.get('report_id', '')
                    if report_id and report_id not in processed_report_ids:
                        all_results.append(row.to_dict())
                        processed_report_ids.add(report_id)
                        new_results += 1
                
                print(f"   📊 Added {new_results} new unique results")
                
            except Exception as e:
                print(f"   ⚠️ No Business_Context_Results sheet: {e}")
            
            # Read the Failed_Reports sheet if it exists
            try:
                df_failed = pd.read_excel(file_path, sheet_name='Failed_Reports')
                if len(df_failed) > 0:
                    print(f"   ⚠️ Found {len(df_failed)} failed reports")
                    for _, row in df_failed.iterrows():
                        report_id = row.get('report_id', '')
                        if report_id and not any(f.get('report_id') == report_id for f in all_failed):
                            all_failed.append(row.to_dict())
            except:
                pass  # No failed reports sheet
                
        except Exception as e:
            print(f"   ❌ Error reading {file_path}: {e}")
    
    print(f"\n📊 COMBINATION SUMMARY:")
    print(f"   • Total unique successful results: {len(all_results)}")
    print(f"   • Total unique failed reports: {len(all_failed)}")
    print(f"   • Total processed: {len(all_results) + len(all_failed)}")
    
    if len(all_results) > 0:
        # Create DataFrames
        results_df = pd.DataFrame(all_results)
        
        # Sort by report_id to ensure proper order
        def extract_report_number(report_id):
            try:
                return int(report_id.replace('Report_', ''))
            except:
                return 0
        
        results_df['_sort_key'] = results_df['report_id'].apply(extract_report_number)
        results_df = results_df.sort_values('_sort_key').drop('_sort_key', axis=1)
        
        print(f"\n🎯 Results range: {results_df.iloc[0]['report_id']} to {results_df.iloc[-1]['report_id']}")
        
        # Create summary data
        total_reports = 1555  # We know this from the original file
        successful = len(all_results)
        failed = len(all_failed)
        success_rate = (successful / total_reports) * 100 if total_reports > 0 else 0
        
        summary_data = {
            'Metric': [
                'Total Reports in Dataset',
                'Successfully Generated Context',
                'Failed to Process',
                'Success Rate (%)',
                'Processing Completion Date',
                'Gemini Model Used',
                'Combined from Multiple Sessions'
            ],
            'Value': [
                total_reports,
                successful,
                failed,
                f"{success_rate:.1f}",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Gemini 2.5 Pro",
                "Yes - Multiple Progress Files"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        # Save combined results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"COMPLETE_metabase_reports_with_business_context_{timestamp}.xlsx"
        
        print(f"\n💾 Saving combined results to: {output_file}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            results_df.to_excel(writer, sheet_name='Business_Context_Results', index=False)
            summary_df.to_excel(writer, sheet_name='Processing_Summary', index=False)
            
            if all_failed:
                failed_df = pd.DataFrame(all_failed)
                failed_df.to_excel(writer, sheet_name='Failed_Reports', index=False)
        
        print(f"✅ Combined file created successfully!")
        print(f"\n📋 Final file contains:")
        print(f"   • Business_Context_Results: {len(results_df)} successfully processed reports")
        print(f"   • Processing_Summary: Complete statistics")
        if all_failed:
            print(f"   • Failed_Reports: {len(all_failed)} failed reports")
        
        return output_file
    else:
        print("❌ No results found to combine!")
        return None

if __name__ == "__main__":
    try:
        output_file = combine_all_results()
        if output_file:
            print(f"\n🎉 SUCCESS! Complete results file: {output_file}")
            print(f"📊 This file contains ALL your processed reports from the entire session.")
        else:
            print(f"\n❌ Failed to create combined file.")
    except Exception as e:
        print(f"\n💥 Error: {e}") 