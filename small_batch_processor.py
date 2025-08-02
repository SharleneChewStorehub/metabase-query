#!/usr/bin/env python3
"""
Small Batch Processor - Process specific number of reports with full verification

This processes only a small, controlled batch of reports (default 20) 
and provides complete verification before and after.
"""

import pandas as pd
import json
import os
import time
import logging
from datetime import datetime
from gemini_business_context_generator import GeminiBusinessContextGenerator

class SmallBatchProcessor:
    """Process small batches with full verification."""
    
    def __init__(self, excel_file: str, batch_size: int = 20):
        self.excel_file = excel_file
        self.batch_size = batch_size
        self.master_file = "MASTER_BULLETPROOF_RESULTS.xlsx"
        self.state_file = "BULLETPROOF_STATE.json"
    
    def get_current_status(self):
        """Get current processing status."""
        processed_reports = set()
        
        if os.path.exists(self.master_file):
            df = pd.read_excel(self.master_file, sheet_name='Business_Context_Results')
            processed_reports = set(df['report_id'].tolist())
        
        # Find missing reports
        df_original = pd.read_excel(self.excel_file)
        total_reports = len(df_original)
        
        processed_numbers = set()
        for report_id in processed_reports:
            try:
                num = int(report_id.replace('Report_', ''))
                processed_numbers.add(num)
            except:
                continue
        
        all_numbers = set(range(1, total_reports + 1))
        missing_numbers = sorted(all_numbers - processed_numbers)
        
        return {
            'total_reports': total_reports,
            'processed_count': len(processed_numbers),
            'missing_count': len(missing_numbers),
            'missing_numbers': missing_numbers,
            'completion_rate': (len(processed_numbers) / total_reports) * 100
        }
    
    def process_batch(self, batch_reports: list):
        """Process a specific batch of report numbers."""
        print(f"🚀 PROCESSING BATCH OF {len(batch_reports)} REPORTS")
        print(f"📊 Reports: {batch_reports[0]}-{batch_reports[-1]}")
        print("=" * 50)
        
        # Get baseline
        baseline_count = 0
        if os.path.exists(self.master_file):
            df_baseline = pd.read_excel(self.master_file, sheet_name='Business_Context_Results')
            baseline_count = len(df_baseline)
        
        print(f"📊 Starting with: {baseline_count} reports")
        
        # Initialize generator
        generator = GeminiBusinessContextGenerator(self.excel_file)
        
        if not generator.setup_gemini_api():
            print("❌ API setup failed")
            return False
        
        if not generator.load_excel_data():
            print("❌ Data loading failed")
            return False
        
        # Process each report in batch
        results = []
        failed = []
        
        for i, report_num in enumerate(batch_reports):
            report_id = f"Report_{report_num}"
            
            try:
                row = generator.df.iloc[report_num - 1]
                report_name = str(row.get('report_name', 'Unknown'))
                description = str(row.get('description', ''))
                sql_query = str(row.get('sql_query', ''))
                
                if not report_name or report_name == 'nan' or not sql_query or sql_query == 'nan':
                    print(f"⚠️ {report_id}: Missing essential data")
                    failed.append({'report_id': report_id, 'error': 'Missing data'})
                    continue
                
                print(f"🤖 Processing {report_id} ({i+1}/{len(batch_reports)})...")
                prompt = generator.create_business_context_prompt(report_name, description, sql_query)
                response = generator.call_gemini_api(prompt, report_id)
                
                if response:
                    parsed_result = generator.parse_gemini_response(response)
                    result = {
                        'report_id': report_id,
                        'original_report_name': report_name,
                        'original_description': description,
                        'original_sql_query': sql_query,
                        **parsed_result,
                        'processing_timestamp': datetime.now().isoformat()
                    }
                    results.append(result)
                    print(f"✅ {report_id}: Success")
                else:
                    print(f"❌ {report_id}: API call failed")
                    failed.append({'report_id': report_id, 'error': 'API failed'})
                
                # Rate limiting
                if i < len(batch_reports) - 1:
                    time.sleep(1.5)
                    
            except Exception as e:
                print(f"❌ {report_id}: Unexpected error - {e}")
                failed.append({'report_id': report_id, 'error': str(e)})
        
        # Save results
        print(f"\n💾 Saving {len(results)} successful results...")
        
        # Load existing data
        all_results = []
        if os.path.exists(self.master_file):
            df_existing = pd.read_excel(self.master_file, sheet_name='Business_Context_Results')
            all_results = df_existing.to_dict('records')
        
        # Add new results
        all_results.extend(results)
        
        # Save using bulletproof mechanism
        temp_file = self.master_file.replace('.xlsx', '_temp.xlsx')
        
        try:
            # Create summary
            total_in_dataset = len(generator.df)
            summary_data = {
                'Metric': [
                    'Total Reports in Dataset',
                    'Successfully Processed',
                    'Failed Reports',
                    'Completion Rate (%)',
                    'Last Updated',
                    'Batch Size',
                    'Last Batch'
                ],
                'Value': [
                    total_in_dataset,
                    len(all_results),
                    len(failed),
                    f"{(len(all_results)/total_in_dataset)*100:.1f}",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    len(results),
                    f"Report_{batch_reports[0]}-{batch_reports[-1]}"
                ]
            }
            
            # Save to temp file first
            with pd.ExcelWriter(temp_file, engine='openpyxl') as writer:
                pd.DataFrame(all_results).to_excel(writer, sheet_name='Business_Context_Results', index=False)
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Processing_Summary', index=False)
                
                if failed:
                    pd.DataFrame(failed).to_excel(writer, sheet_name='Failed_Reports', index=False)
            
            # Atomic rename
            os.rename(temp_file, self.master_file)
            print("✅ Excel save successful")
            
            # Save state
            processed_reports = [r['report_id'] for r in all_results]
            state_data = {
                'processed_reports': processed_reports,
                'failed_reports': failed,
                'last_save': datetime.now().isoformat(),
                'total_processed': len(all_results),
                'last_batch': batch_reports
            }
            
            state_temp = self.state_file.replace('.json', '_temp.json')
            with open(state_temp, 'w') as f:
                json.dump(state_data, f, indent=2)
            os.rename(state_temp, self.state_file)
            
            print("✅ State save successful")
            
        except Exception as e:
            print(f"❌ Save failed: {e}")
            return False
        
        # Verify the save
        df_verify = pd.read_excel(self.master_file, sheet_name='Business_Context_Results')
        expected_total = baseline_count + len(results)
        
        if len(df_verify) == expected_total:
            print(f"✅ VERIFICATION SUCCESS!")
            print(f"   • Started with: {baseline_count} reports")
            print(f"   • Processed: {len(results)} reports successfully") 
            print(f"   • Failed: {len(failed)} reports")
            print(f"   • Final total: {len(df_verify)} reports")
            
            # Verify specific reports are there
            report_ids = df_verify['report_id'].tolist()
            expected_reports = [f'Report_{num}' for num in batch_reports if f'Report_{num}' in [r['report_id'] for r in results]]
            found_reports = [rid for rid in expected_reports if rid in report_ids]
            
            print(f"   • Verified saved: {len(found_reports)}/{len(expected_reports)} batch reports")
            return True
        else:
            print(f"❌ VERIFICATION FAILED!")
            print(f"   • Expected: {expected_total} reports")
            print(f"   • Got: {len(df_verify)} reports")
            return False

def main():
    """Run small batch processor."""
    print("🔧 SMALL BATCH PROCESSOR")
    print("=" * 40)
    print("🎯 Process reports in small, verifiable batches")
    print("🔒 Full verification before and after each batch")
    print("=" * 40)
    
    processor = SmallBatchProcessor("metabase_reports_detailed_20250731_122354.xlsx", batch_size=20)
    
    # Get current status
    status = processor.get_current_status()
    
    print(f"\n📊 CURRENT STATUS:")
    print(f"   • Total reports: {status['total_reports']}")
    print(f"   • Completed: {status['processed_count']}")
    print(f"   • Missing: {status['missing_count']}")
    print(f"   • Progress: {status['completion_rate']:.1f}%")
    
    if not status['missing_numbers']:
        print("🎉 ALL REPORTS COMPLETE!")
        return
    
    # Show next batch
    next_batch = status['missing_numbers'][:20]  # Next 20 missing reports
    print(f"\n🎯 NEXT BATCH READY:")
    print(f"   • Reports: {next_batch[0]}-{next_batch[-1]}")
    print(f"   • Count: {len(next_batch)} reports")
    print(f"   • Estimated time: {len(next_batch) * 0.5:.0f} minutes")
    
    # Confirm before processing
    response = input("\nProcess this batch? (y/n): ").lower()
    if response != 'y':
        print("❌ Cancelled by user")
        return
    
    # Process the batch
    if processor.process_batch(next_batch):
        print("\n🎉 BATCH COMPLETED SUCCESSFULLY!")
        
        # Show updated status
        new_status = processor.get_current_status()
        print(f"\n📊 UPDATED STATUS:")
        print(f"   • Completed: {new_status['processed_count']}")
        print(f"   • Remaining: {new_status['missing_count']}")
        print(f"   • Progress: {new_status['completion_rate']:.1f}%")
        
        if new_status['missing_count'] > 0:
            print(f"\n💡 Run script again to process next batch")
        else:
            print(f"\n🎉 ALL REPORTS COMPLETE!")
    else:
        print("\n❌ BATCH FAILED!")

if __name__ == "__main__":
    main() 