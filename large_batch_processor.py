#!/usr/bin/env python3
"""
Large Batch Processor - 100 reports with EXTREME data protection

Features:
- Processes 100 reports per batch
- Saves every 10 reports (automatic checkpoints)
- Emergency crash recovery
- Multiple backup mechanisms
- Real-time progress tracking
- Cursor crash protection
"""

import pandas as pd
import json
import os
import time
import logging
import signal
import sys
from datetime import datetime
from gemini_business_context_generator import GeminiBusinessContextGenerator

class LargeBatchProcessor:
    """Process large batches with extreme data protection."""
    
    def __init__(self, excel_file: str, batch_size: int = 100):
        self.excel_file = excel_file
        self.batch_size = batch_size
        self.master_file = "MASTER_BULLETPROOF_RESULTS.xlsx"
        self.state_file = "BULLETPROOF_STATE.json"
        self.emergency_backup_dir = "EMERGENCY_BACKUPS"
        self.checkpoint_frequency = 10  # Save every 10 reports
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
                logging.FileHandler('large_batch_processor.log'),
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
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Save 1: JSON backup (fastest)
            json_backup = os.path.join(self.emergency_backup_dir, f"emergency_results_{timestamp}.json")
            emergency_data = {
                'results': results_so_far,
                'batch_info': batch_info,
                'timestamp': timestamp,
                'total_saved': len(results_so_far)
            }
            with open(json_backup, 'w') as f:
                json.dump(emergency_data, f, indent=2)
            print(f"🆘 Emergency JSON backup: {json_backup}")
            
            # Save 2: CSV backup (human readable)
            if results_so_far:
                csv_backup = os.path.join(self.emergency_backup_dir, f"emergency_results_{timestamp}.csv")
                pd.DataFrame(results_so_far).to_csv(csv_backup, index=False)
                print(f"🆘 Emergency CSV backup: {csv_backup}")
            
            # Save 3: Excel backup (full format)
            if results_so_far:
                excel_backup = os.path.join(self.emergency_backup_dir, f"emergency_results_{timestamp}.xlsx")
                with pd.ExcelWriter(excel_backup, engine='openpyxl') as writer:
                    pd.DataFrame(results_so_far).to_excel(writer, sheet_name='Emergency_Results', index=False)
                print(f"🆘 Emergency Excel backup: {excel_backup}")
            
            print(f"✅ Emergency save complete: {len(results_so_far)} results secured")
            return True
            
        except Exception as e:
            print(f"❌ Emergency save failed: {e}")
            return False
    
    def save_checkpoint(self, all_results: list, checkpoint_num: int, batch_info: dict):
        """Save checkpoint every 10 reports."""
        try:
            # Update master file
            temp_file = self.master_file.replace('.xlsx', '_temp.xlsx')
            
            # Create summary
            df_original = pd.read_excel(self.excel_file)
            total_in_dataset = len(df_original)
            summary_data = {
                'Metric': [
                    'Total Reports in Dataset',
                    'Successfully Processed',
                    'Completion Rate (%)',
                    'Last Updated',
                    'Checkpoint Number',
                    'Batch Info'
                ],
                'Value': [
                    total_in_dataset,
                    len(all_results),
                    f"{(len(all_results)/total_in_dataset)*100:.1f}",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    checkpoint_num,
                    f"Batch {batch_info['start']}-{batch_info['end']}"
                ]
            }
            
            # Save to temp file first
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
                'batch_info': batch_info
            }
            
            state_temp = self.state_file.replace('.json', '_temp.json')
            with open(state_temp, 'w') as f:
                json.dump(state_data, f, indent=2)
            os.rename(state_temp, self.state_file)
            
            print(f"💾 Checkpoint {checkpoint_num} saved: {len(all_results)} total reports")
            return True
            
        except Exception as e:
            print(f"❌ Checkpoint save failed: {e}")
            return False
    
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
    
    def process_large_batch(self, batch_reports: list):
        """Process large batch with extreme data protection."""
        batch_info = {
            'start': batch_reports[0],
            'end': batch_reports[-1],
            'size': len(batch_reports),
            'start_time': datetime.now().isoformat()
        }
        
        print(f"🚀 PROCESSING LARGE BATCH: {len(batch_reports)} REPORTS")
        print(f"📊 Reports: {batch_reports[0]}-{batch_reports[-1]}")
        print(f"💾 Auto-save every {self.checkpoint_frequency} reports")
        print(f"🆘 Emergency backups enabled")
        print("=" * 60)
        
        # Get baseline
        baseline_count = 0
        all_existing_results = []
        if os.path.exists(self.master_file):
            df_baseline = pd.read_excel(self.master_file, sheet_name='Business_Context_Results')
            baseline_count = len(df_baseline)
            all_existing_results = df_baseline.to_dict('records')
        
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
        new_results = []
        failed = []
        checkpoint_count = 0
        
        for i, report_num in enumerate(batch_reports):
            if self.interrupted:
                print(f"\n🛑 INTERRUPT HANDLING...")
                self.emergency_save(new_results, batch_info)
                print(f"✅ All progress saved before exit")
                print(f"🔄 Run script again to continue from where you left off")
                sys.exit(0)
            
            report_id = f"Report_{report_num}"
            
            try:
                row = generator.df.iloc[report_num - 1]
                report_name = str(row.get('report_name', 'Unknown'))
                description = str(row.get('description', ''))
                sql_query = str(row.get('sql_query', ''))
                
                if not report_name or report_name == 'nan' or not sql_query or sql_query == 'nan':
                    print(f"⚠️ {report_id}: Missing essential data ({i+1}/{len(batch_reports)})")
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
                    new_results.append(result)
                    print(f"✅ {report_id}: Success")
                else:
                    print(f"❌ {report_id}: API call failed")
                    failed.append({'report_id': report_id, 'error': 'API failed'})
                
                # CHECKPOINT SAVE - Every 10 reports
                if len(new_results) > 0 and len(new_results) % self.checkpoint_frequency == 0:
                    checkpoint_count += 1
                    current_total = all_existing_results + new_results
                    
                    print(f"\n💾 CHECKPOINT {checkpoint_count} - Saving progress...")
                    if self.save_checkpoint(current_total, checkpoint_count, batch_info):
                        print(f"✅ Checkpoint saved: {len(new_results)} new + {baseline_count} existing = {len(current_total)} total")
                    else:
                        print(f"❌ Checkpoint failed - creating emergency backup...")
                        self.emergency_save(new_results, batch_info)
                    print()
                
                # Rate limiting
                if i < len(batch_reports) - 1:
                    time.sleep(1.5)
                
                # Progress update
                progress = ((i + 1) / len(batch_reports)) * 100
                remaining = len(batch_reports) - (i + 1)
                eta_minutes = remaining * 0.5
                print(f"📊 Batch progress: {i+1}/{len(batch_reports)} ({progress:.1f}%) - ETA: {eta_minutes:.0f}min")
                    
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
        
        # Verification
        df_verify = pd.read_excel(self.master_file, sheet_name='Business_Context_Results')
        expected_total = baseline_count + len(new_results)
        
        if len(df_verify) == expected_total:
            print(f"✅ VERIFICATION SUCCESS!")
            print(f"   • Started with: {baseline_count} reports")
            print(f"   • Processed: {len(new_results)} reports successfully") 
            print(f"   • Failed: {len(failed)} reports")
            print(f"   • Final total: {len(df_verify)} reports")
            print(f"   • Checkpoints saved: {checkpoint_count}")
            return True
        else:
            print(f"❌ VERIFICATION FAILED!")
            print(f"   • Expected: {expected_total} reports")
            print(f"   • Got: {len(df_verify)} reports")
            print(f"🆘 Emergency backups available in {self.emergency_backup_dir}/")
            return False

def main():
    """Run large batch processor."""
    print("🔥 LARGE BATCH PROCESSOR - 100 REPORTS")
    print("=" * 50)
    print("🎯 Process 100 reports per batch")
    print("💾 Auto-save every 10 reports") 
    print("🆘 Emergency crash protection")
    print("🔒 Multiple backup mechanisms")
    print("=" * 50)
    
    processor = LargeBatchProcessor("metabase_reports_detailed_20250731_122354.xlsx", batch_size=100)
    
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
    next_batch = status['missing_numbers'][:100]  # Next 100 missing reports
    print(f"\n🎯 NEXT LARGE BATCH READY:")
    print(f"   • Reports: {next_batch[0]}-{next_batch[-1]}")
    print(f"   • Count: {len(next_batch)} reports")
    print(f"   • Estimated time: {len(next_batch) * 0.5:.0f} minutes")
    print(f"   • Checkpoints: Every 10 reports")
    
    # Confirm before processing
    response = input("\nProcess this large batch? (y/n): ").lower()
    if response != 'y':
        print("❌ Cancelled by user")
        return
    
    # Process the batch
    if processor.process_large_batch(next_batch):
        print("\n🎉 LARGE BATCH COMPLETED SUCCESSFULLY!")
        
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
        print("\n❌ LARGE BATCH FAILED!")
        print(f"🆘 Check emergency backups in {processor.emergency_backup_dir}/")

if __name__ == "__main__":
    main() 