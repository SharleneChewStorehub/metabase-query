#!/usr/bin/env python3
"""
Create Final Mapped Results - Map processed data to actual Metabase report IDs
"""

import pandas as pd
from datetime import datetime

def create_final_mapped_results():
    """Create final results file with proper Metabase report ID mapping."""
    
    print("🔄 CREATING FINAL MAPPED RESULTS FILE")
    print("=" * 50)
    
    # Read original data (for ID mapping)
    print("📖 Loading original data...")
    df_original = pd.read_excel('metabase_reports_detailed_20250731_122354.xlsx')
    print(f"✅ Loaded {len(df_original)} original reports")
    
    # Read processed results
    print("📖 Loading processed results...")
    df_processed = pd.read_excel('MASTER_BULLETPROOF_RESULTS.xlsx', sheet_name='Business_Context_Results')
    print(f"✅ Loaded {len(df_processed)} processed reports")
    
    # Create mapping from row number to actual Metabase ID
    print("🔗 Creating ID mapping...")
    metabase_id_mapping = {}
    
    for _, row in df_processed.iterrows():
        row_based_id = row['report_id']  # e.g., "Report_799"
        
        # Extract row number from "Report_XXX"
        try:
            row_number = int(row_based_id.replace('Report_', ''))
            # Get actual Metabase ID from original data (1-indexed to 0-indexed)
            if row_number <= len(df_original):
                actual_metabase_id = df_original.iloc[row_number - 1]['report_id']
                metabase_id_mapping[row_based_id] = actual_metabase_id
            else:
                print(f"⚠️ Warning: Row {row_number} not found in original data")
                metabase_id_mapping[row_based_id] = None
        except Exception as e:
            print(f"❌ Error processing {row_based_id}: {e}")
            metabase_id_mapping[row_based_id] = None
    
    print(f"✅ Created mapping for {len(metabase_id_mapping)} reports")
    
    # Apply mapping to processed results
    print("🔄 Applying Metabase ID mapping...")
    df_final = df_processed.copy()
    
    # Add actual Metabase ID column
    df_final['metabase_report_id'] = df_final['report_id'].map(metabase_id_mapping)
    
    # Reorder columns to put metabase_report_id first
    cols = ['metabase_report_id'] + [col for col in df_final.columns if col != 'metabase_report_id']
    df_final = df_final[cols]
    
    # Create summary statistics
    successful_mappings = df_final['metabase_report_id'].notna().sum()
    print(f"✅ Successfully mapped {successful_mappings} reports to Metabase IDs")
    
    # Create final filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_filename = f"FINAL_METABASE_REPORTS_WITH_BUSINESS_CONTEXT_{timestamp}.xlsx"
    
    # Create summary data
    summary_data = {
        'Metric': [
            'Total Reports Processed',
            'Successfully Mapped to Metabase IDs',
            'Completion Rate (%)',
            'Processing Date',
            'Original Data Source',
            'Final Output File'
        ],
        'Value': [
            len(df_final),
            successful_mappings,
            f"{(successful_mappings/len(df_final))*100:.1f}",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metabase_reports_detailed_20250731_122354.xlsx",
            final_filename
        ]
    }
    
    # Save final file
    print(f"💾 Saving final results to {final_filename}...")
    with pd.ExcelWriter(final_filename, engine='openpyxl') as writer:
        df_final.to_excel(writer, sheet_name='Final_Results_With_Metabase_IDs', index=False)
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Processing_Summary', index=False)
    
    print("✅ FINAL MAPPED RESULTS CREATED SUCCESSFULLY!")
    print(f"📁 File: {final_filename}")
    print(f"📊 Reports: {len(df_final)}")
    print(f"🔗 Metabase ID mappings: {successful_mappings}")
    print(f"📋 Columns: {list(df_final.columns)}")
    
    return final_filename

if __name__ == "__main__":
    create_final_mapped_results() 