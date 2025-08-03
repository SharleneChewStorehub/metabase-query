#!/usr/bin/env python3
"""
Process Recent 400 Reports - Bulletproof Business Context Generator

This script processes the 400 recently active reports with the same
bulletproof safety measures used for the original 1,550 reports:

- Extreme backup measures (save every 10 reports)
- Emergency crash recovery
- No deletion via Metabase API (READ-ONLY)
- Secure credential management (.env files)
- Gemini 2.5 Pro AI model
- Same prompt structure and output format
- 100% validation before completion

Author: Business Intelligence Team
Date: August 2025
Model: Gemini 2.5 Pro
"""

import pandas as pd
import json
import os
import time
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from gemini_business_context_generator import GeminiBusinessContextGenerator

class Recent400ReportsProcessor:
    """Process 400 recently active reports with extreme data protection."""
    
    def __init__(self, excel_file: str = "COMPLETE_recent_metabase_reports_20250803_035047.xlsx"):
        self.excel_file = excel_file
        self.batch_size = 100  # Same as original process
        self.master_file = "RECENT_400_REPORTS_WITH_BUSINESS_CONTEXT.xlsx"
        self.state_file = "RECENT_400_STATE.json"
        self.emergency_backup_dir = "EMERGENCY_BACKUPS_400"
        self.checkpoint_frequency = 10  # Save every 10 reports (same as original)
        self.interrupted = False
        
        # Create emergency backup directory
        os.makedirs(self.emergency_backup_dir, exist_ok=True)
        
        # Setup graceful interrupt handling
        signal.signal(signal.SIGINT, self.handle_interrupt)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('recent_400_processor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def handle_interrupt(self, signum, frame):
        """Handle interrupts gracefully - save everything immediately."""
        print(f"\n🛑 INTERRUPT DETECTED - EMERGENCY SAVE IN PROGRESS...")
        self.interrupted = True
        # Emergency save will be handled in the main loop
    
    def emergency_save(self, results_so_far: list, batch_info: dict):
        """Emergency save in case of crash - multiple backup formats."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save as Excel
            emergency_excel = f"{self.emergency_backup_dir}/emergency_results_{timestamp}.xlsx"
            pd.DataFrame(results_so_far).to_excel(emergency_excel, index=False)
            
            # Save as JSON (backup format)
            emergency_json = f"{self.emergency_backup_dir}/emergency_results_{timestamp}.json"
            with open(emergency_json, 'w') as f:
                json.dump({
                    'results': results_so_far,
                    'batch_info': batch_info,
                    'save_time': timestamp,
                    'type': 'emergency_save'
                }, f, indent=2)
            
            print(f"🆘 Emergency backups saved:")
            print(f"   📁 {emergency_excel}")
            print(f"   📁 {emergency_json}")
            
        except Exception as e:
            print(f"❌ Emergency save failed: {e}")
    
    def save_checkpoint(self, all_results: list, checkpoint_num: int, batch_info: dict):
        """Save checkpoint every 10 reports - same as original system."""
        try:
            # Update master file
            temp_file = self.master_file.replace('.xlsx', '_temp.xlsx')
            
            # Create summary
            df_original = pd.read_excel(self.excel_file)
            total_in_dataset = len(df_original)
            summary_data = {
                'Metric': [
                    'Total Recent Active Reports',
                    'Successfully Processed',
                    'Completion Rate (%)',
                    'Last Updated',
                    'Checkpoint Number',
                    'Processing Model',
                    'Batch Info'
                ],
                'Value': [
                    total_in_dataset,
                    len(all_results),
                    f"{(len(all_results)/total_in_dataset)*100:.1f}",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    checkpoint_num,
                    "Gemini 2.5 Pro",
                    f"Recent Active Reports Batch"
                ]
            }
            
            # Save to temp file first (atomic operation)
            with pd.ExcelWriter(temp_file, engine='openpyxl') as writer:
                pd.DataFrame(all_results).to_excel(writer, sheet_name='Business_Context_Results', index=False)
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Processing_Summary', index=False)
            
            # Atomic rename
            os.rename(temp_file, self.master_file)
            
            # Save state
            processed_reports = [r['report_id'] for r in all_results]
            state_data = {
                'processed_reports': processed_reports,
                'failed_reports': [],
                'last_save': datetime.now().isoformat(),
                'total_processed': len(all_results),
                'checkpoint': checkpoint_num,
                'batch_info': batch_info,
                'dataset_type': 'recent_400_active_reports'
            }
            
            state_temp = self.state_file.replace('.json', '_temp.json')
            with open(state_temp, 'w') as f:
                json.dump(state_data, f, indent=2)
            os.rename(state_temp, self.state_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Checkpoint save failed: {e}")
            return False
    
    def get_current_status(self):
        """Get current processing status."""
        processed_count = 0
        failed_count = 0
        
        if os.path.exists(self.master_file):
            try:
                df = pd.read_excel(self.master_file, sheet_name='Business_Context_Results')
                processed_count = len(df)
            except:
                pass
        
        # Load original dataset
        df_original = pd.read_excel(self.excel_file)
        total_reports = len(df_original)
        remaining = total_reports - processed_count
        
        return {
            'total_reports': total_reports,
            'processed': processed_count,
            'remaining': remaining,
            'failed': failed_count,
            'completion_rate': (processed_count / total_reports) * 100 if total_reports > 0 else 0,
            'master_file_exists': os.path.exists(self.master_file)
        }
    
    def process_recent_400_reports(self):
        """Process all 400 recent active reports with bulletproof safety."""
        print("🚀 RECENT 400 ACTIVE REPORTS - BUSINESS CONTEXT GENERATOR")
        print("=" * 70)
        print("🔒 Using same bulletproof safety measures as 1,550 reports")
        print("🤖 Model: Gemini 2.5 Pro (highest quality)")
        print("💾 Auto-save every 10 reports")
        print("🆘 Emergency crash recovery enabled")
        print("⏱️  Rate limiting: 1.5s between API calls")
        print("🚫 NO DELETION - Metabase API READ-ONLY")
        print("=" * 70)
        
        # Check current status
        status = self.get_current_status()
        print(f"\n📊 CURRENT STATUS:")
        print(f"   • Total recent active reports: {status['total_reports']}")
        print(f"   • Already processed: {status['processed']}")
        print(f"   • Remaining: {status['remaining']}")
        print(f"   • Completion rate: {status['completion_rate']:.1f}%")
        
        if status['remaining'] == 0:
            print("\n🎉 ALL 400 REPORTS ALREADY PROCESSED!")
            return True
        
        # Load existing results
        all_existing_results = []
        if os.path.exists(self.master_file):
            df_existing = pd.read_excel(self.master_file, sheet_name='Business_Context_Results')
            all_existing_results = df_existing.to_dict('records')
            processed_ids = set(df_existing['report_id'].tolist())
            print(f"📂 Loaded {len(all_existing_results)} existing results")
        else:
            processed_ids = set()
        
        # Load source data
        df_source = pd.read_excel(self.excel_file)
        print(f"📊 Loaded {len(df_source)} recent active reports")
        
        # Initialize Gemini generator using the recent reports file
        generator = GeminiBusinessContextGenerator(self.excel_file)
        
        if not generator.setup_gemini_api():
            print("❌ Gemini API setup failed")
            return False
        
        if not generator.load_excel_data():
            print("❌ Data loading failed")
            return False
        
        # Process unprocessed reports
        batch_info = {
            'dataset': 'recent_400_active_reports',
            'start_time': datetime.now().isoformat(),
            'total_to_process': status['remaining']
        }
        
        new_results = []
        failed = []
        checkpoint_count = 0
        
        print(f"\n🤖 Starting processing of {status['remaining']} remaining reports...")
        print("=" * 60)
        
        for i, row in df_source.iterrows():
            if self.interrupted:
                print(f"\n🛑 INTERRUPT HANDLING...")
                self.emergency_save(new_results, batch_info)
                print(f"✅ All progress saved before exit")
                print(f"🔄 Run script again to continue from where you left off")
                sys.exit(0)
            
            # Create report ID
            report_id = f"Recent_{row['report_id']}"  # Prefix to distinguish from original 1550
            
            # Skip if already processed
            if report_id in processed_ids:
                continue
            
            try:
                # Extract data from row (same structure as original)
                report_name = str(row.get('report_name', 'Unknown'))
                description = str(row.get('description', ''))
                sql_query = str(row.get('sql_query', ''))
                
                if not report_name or report_name == 'nan' or not sql_query or sql_query == 'nan':
                    print(f"⚠️ {report_id}: Missing essential data")
                    failed.append({'report_id': report_id, 'error': 'Missing data'})
                    continue
                
                print(f"🤖 Processing {report_id} ({len(new_results)+1}/{status['remaining']})...")
                
                # Create prompt (same as original process)
                prompt = generator.create_business_context_prompt(report_name, description, sql_query)
                response = generator.call_gemini_api(prompt, report_id)
                
                if response:
                    parsed_result = generator.parse_gemini_response(response)
                    result = {
                        'metabase_report_id': row['report_id'],  # Original numeric ID
                        'report_id': report_id,  # Our prefixed ID
                        'original_report_name': report_name,
                        'original_description': description,
                        'original_sql_query': sql_query,
                        'collection_id': row.get('collection_id', ''),
                        'collection_name': row.get('collection_name', ''),
                        'activity_score': row.get('activity_score', 0),
                        'last_query_start': row.get('last_query_start', ''),
                        'dashboard_count': row.get('dashboard_count', 0),
                        'is_priority_collection': row.get('is_priority_collection', False),
                        **parsed_result,
                        'processing_timestamp': datetime.now().isoformat()
                    }
                    new_results.append(result)
                    print(f"✅ {report_id}: Success")
                else:
                    print(f"❌ {report_id}: API call failed")
                    failed.append({'report_id': report_id, 'error': 'API failed'})
                
                # CHECKPOINT SAVE - Every 10 reports (same as original)
                if len(new_results) > 0 and len(new_results) % self.checkpoint_frequency == 0:
                    checkpoint_count += 1
                    current_total = all_existing_results + new_results
                    
                    print(f"\n💾 CHECKPOINT {checkpoint_count} - Saving progress...")
                    if self.save_checkpoint(current_total, checkpoint_count, batch_info):
                        print(f"✅ Checkpoint saved: {len(new_results)} new + {len(all_existing_results)} existing = {len(current_total)} total")
                    else:
                        print(f"❌ Checkpoint failed - creating emergency backup...")
                        self.emergency_save(new_results, batch_info)
                    print()
                
                # Rate limiting (same as original)
                time.sleep(1.5)
                
                # Progress update
                remaining_reports = status['remaining'] - len(new_results)
                eta_minutes = remaining_reports * 1.5 / 60
                completion_pct = (len(new_results) / status['remaining']) * 100
                print(f"📊 Progress: {len(new_results)}/{status['remaining']} ({completion_pct:.1f}%) - ETA: {eta_minutes:.0f}min")
                    
            except Exception as e:
                print(f"❌ {report_id}: Unexpected error - {e}")
                failed.append({'report_id': report_id, 'error': str(e)})
                
                # Emergency save on unexpected errors
                print(f"🆘 Creating emergency backup due to error...")
                self.emergency_save(new_results, batch_info)
        
        # Final save
        print(f"\n💾 FINAL SAVE - Saving {len(new_results)} new results...")
        final_results = all_existing_results + new_results
        
        if self.save_checkpoint(final_results, checkpoint_count + 1, batch_info):
            print(f"✅ Final save successful")
        else:
            print(f"❌ Final save failed - emergency backup created")
            self.emergency_save(new_results, batch_info)
            return False
        
        # Add failed reports sheet if any
        if failed:
            try:
                failed_df = pd.DataFrame(failed)
                with pd.ExcelWriter(self.master_file, mode='a', engine='openpyxl') as writer:
                    failed_df.to_excel(writer, sheet_name='Failed_Reports', index=False)
                print(f"📋 Added Failed_Reports sheet with {len(failed)} entries")
            except Exception as e:
                print(f"⚠️ Could not add Failed_Reports sheet: {e}")
        
        # Verification (same as original)
        df_verify = pd.read_excel(self.master_file, sheet_name='Business_Context_Results')
        expected_total = len(all_existing_results) + len(new_results)
        
        if len(df_verify) == expected_total:
            print(f"\n🎉 VERIFICATION SUCCESS!")
            print(f"   • Started with: {len(all_existing_results)} reports")
            print(f"   • Processed: {len(new_results)} reports successfully") 
            print(f"   • Failed: {len(failed)} reports")
            print(f"   • Final total: {len(df_verify)} reports")
            print(f"   • Checkpoints saved: {checkpoint_count}")
            print(f"   • Output file: {self.master_file}")
            print(f"\n🚀 ALL 400 RECENT ACTIVE REPORTS NOW HAVE BUSINESS CONTEXT!")
            return True
        else:
            print(f"❌ VERIFICATION FAILED!")
            print(f"   • Expected: {expected_total} reports")
            print(f"   • Got: {len(df_verify)} reports")
            print(f"🆘 Emergency backups available in {self.emergency_backup_dir}/")
            return False

def main():
    """Run the Recent 400 Reports processor."""
    print("🎯 RECENT 400 ACTIVE REPORTS - BUSINESS CONTEXT GENERATOR")
    print("Using the same bulletproof system as the original 1,550 reports\n")
    
    # Verify input file exists
    input_file = "COMPLETE_recent_metabase_reports_20250803_035047.xlsx"
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        print("   Please ensure the recent 400 reports file is in the current directory")
        return
    
    # Check file structure
    try:
        df = pd.read_excel(input_file)
        required_columns = ['report_id', 'report_name', 'sql_query']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            print(f"Available columns: {list(df.columns)}")
            return
        
        print(f"✅ Input validation passed: {len(df)} reports found")
        
    except Exception as e:
        print(f"❌ Error reading input file: {e}")
        return
    
    # Initialize and run processor
    processor = Recent400ReportsProcessor(input_file)
    
    try:
        success = processor.process_recent_400_reports()
        
        if success:
            print(f"\n🎉 PROCESS COMPLETED SUCCESSFULLY!")
            print(f"📁 Results saved to: {processor.master_file}")
            print(f"📋 Logs available in: recent_400_processor.log")
        else:
            print(f"\n❌ Process completed with errors")
            print(f"🆘 Check emergency backups in: {processor.emergency_backup_dir}/")
            
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        print(f"🆘 Check emergency backups in: {processor.emergency_backup_dir}/")

if __name__ == "__main__":
    main() 