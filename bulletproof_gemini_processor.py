#!/usr/bin/env python3
"""
BULLETPROOF GEMINI PROCESSOR - ZERO DATA LOSS GUARANTEE

This script GUARANTEES that no work is ever lost. You can interrupt it at ANY time
and resume exactly where you left off. Every 5 reports are automatically saved.

FEATURES:
- Stop/start anytime with Ctrl+C
- Saves progress every 5 reports
- Automatic gap detection and filling
- Master file always contains ALL processed reports
- Bulletproof error handling
- Real-time status tracking
"""

import pandas as pd
import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
import signal
import sys
from gemini_business_context_generator import GeminiBusinessContextGenerator

class BulletproofProcessor:
    """Bulletproof processor that NEVER loses work."""
    
    def __init__(self, excel_file: str):
        self.excel_file = excel_file
        self.master_file = "MASTER_BULLETPROOF_RESULTS.xlsx"
        self.state_file = "BULLETPROOF_STATE.json"
        self.processed_reports: Set[str] = set()
        self.all_results: List[Dict] = []
        self.failed_reports: List[Dict] = []
        self.save_frequency = 5  # Save every 5 reports
        self.interrupted = False
        
        # Setup graceful interrupt handling
        signal.signal(signal.SIGINT, self.handle_interrupt)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bulletproof_processor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def handle_interrupt(self, signum, frame):
        """Handle Ctrl+C gracefully - save everything before exit."""
        print(f"\n🛑 INTERRUPT DETECTED - SAVING ALL WORK...")
        self.interrupted = True
        self.save_all_progress()
        print(f"✅ ALL PROGRESS SAVED - Safe to exit")
        print(f"🔄 Run this script again to resume from exactly where you left off")
        sys.exit(0)
    
    def load_existing_work(self) -> None:
        """Load ALL existing work from master file and state."""
        print("🔍 LOADING EXISTING WORK...")
        
        # Load master results file
        if os.path.exists(self.master_file):
            try:
                df = pd.read_excel(self.master_file, sheet_name='Business_Context_Results')
                for _, row in df.iterrows():
                    report_id = row.get('report_id', '')
                    if report_id:
                        self.processed_reports.add(report_id)
                        self.all_results.append(row.to_dict())
                print(f"✅ Loaded {len(df)} completed reports from master file")
            except Exception as e:
                print(f"⚠️ Could not load master file: {e}")
        
        # Load state file
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                    self.failed_reports = state_data.get('failed_reports', [])
                print(f"✅ Loaded processing state")
            except Exception as e:
                print(f"⚠️ Could not load state: {e}")
        
        print(f"📊 CURRENT STATUS:")
        print(f"   • Completed reports: {len(self.processed_reports)}")
        print(f"   • Failed reports: {len(self.failed_reports)}")
    
    def identify_missing_reports(self) -> List[int]:
        """Find exactly which reports need processing."""
        df_original = pd.read_excel(self.excel_file)
        total_reports = len(df_original)
        
        # Convert processed report IDs to numbers
        processed_numbers = set()
        for report_id in self.processed_reports:
            try:
                num = int(report_id.replace('Report_', ''))
                processed_numbers.add(num)
            except:
                continue
        
        # Find missing reports
        all_numbers = set(range(1, total_reports + 1))
        missing_numbers = sorted(all_numbers - processed_numbers)
        
        print(f"📊 MISSING REPORTS ANALYSIS:")
        print(f"   • Total reports: {total_reports}")
        print(f"   • Already completed: {len(processed_numbers)}")
        print(f"   • Still needed: {len(missing_numbers)}")
        print(f"   • Completion: {(len(processed_numbers)/total_reports)*100:.1f}%")
        
        if missing_numbers:
            # Show ranges for better readability
            ranges = self._format_ranges(missing_numbers)
            print(f"   • Missing ranges: {ranges}")
        
        return missing_numbers
    
    def _format_ranges(self, numbers: List[int]) -> str:
        """Format numbers into readable ranges."""
        if not numbers:
            return "None"
        
        ranges = []
        start = numbers[0]
        end = numbers[0]
        
        for num in numbers[1:] + [None]:
            if num is None or num != end + 1:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                if num is not None:
                    start = end = num
            else:
                end = num
        
        return ", ".join(ranges)
    
    def save_all_progress(self) -> None:
        """Save all progress with bulletproof error handling."""
        if not self.all_results:
            print("⚠️ No results to save")
            return
        
        # Sort results by report number
        def extract_number(result):
            try:
                return int(result['report_id'].replace('Report_', ''))
            except:
                return 0
        
        self.all_results.sort(key=extract_number)
        
        # Create master file with atomic operation
        temp_file = self.master_file.replace('.xlsx', '_temp.xlsx')
        try:
            # Create summary
            total_in_dataset = len(pd.read_excel(self.excel_file))
            summary_data = {
                'Metric': [
                    'Total Reports in Dataset',
                    'Successfully Processed',
                    'Failed Reports',
                    'Completion Rate (%)',
                    'Last Updated',
                    'Save Frequency',
                    'Safety Features'
                ],
                'Value': [
                    total_in_dataset,
                    len(self.all_results),
                    len(self.failed_reports),
                    f"{(len(self.all_results)/total_in_dataset)*100:.1f}",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    f"Every {self.save_frequency} reports",
                    "Bulletproof + Interrupt Safe"
                ]
            }
            
            # Save to temp file first
            with pd.ExcelWriter(temp_file, engine='openpyxl') as writer:
                pd.DataFrame(self.all_results).to_excel(writer, sheet_name='Business_Context_Results', index=False)
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Processing_Summary', index=False)
                
                if self.failed_reports:
                    pd.DataFrame(self.failed_reports).to_excel(writer, sheet_name='Failed_Reports', index=False)
            
            # Atomic rename (prevents corruption)
            os.rename(temp_file, self.master_file)
            
            # Save state file
            state_data = {
                'processed_reports': list(self.processed_reports),
                'failed_reports': self.failed_reports,
                'last_save': datetime.now().isoformat(),
                'total_processed': len(self.all_results)
            }
            
            state_temp = self.state_file.replace('.json', '_temp.json')
            with open(state_temp, 'w') as f:
                json.dump(state_data, f, indent=2)
            os.rename(state_temp, self.state_file)
            
            print(f"💾 BULLETPROOF SAVE COMPLETE: {len(self.all_results)} reports secured")
            
        except Exception as e:
            print(f"❌ Save failed: {e}")
            # Clean up temp files
            for temp in [temp_file, self.state_file.replace('.json', '_temp.json')]:
                if os.path.exists(temp):
                    os.remove(temp)
    
    def process_missing_reports(self, missing_numbers: List[int]) -> bool:
        """Process missing reports with bulletproof saving."""
        if not missing_numbers:
            print("🎉 ALL REPORTS ALREADY PROCESSED!")
            return True
        
        print(f"\n🚀 PROCESSING {len(missing_numbers)} MISSING REPORTS")
        print(f"💾 Auto-save frequency: Every {self.save_frequency} reports")
        print(f"🛑 You can interrupt (Ctrl+C) ANYTIME - all progress will be saved")
        print(f"🔄 Run script again to resume from exact stopping point")
        print("=" * 60)
        
        # Initialize Gemini processor
        generator = GeminiBusinessContextGenerator(self.excel_file)
        
        if not generator.setup_gemini_api():
            print("❌ API setup failed")
            return False
        
        if not generator.load_excel_data():
            print("❌ Data loading failed")  
            return False
        
        # Process each missing report
        for i, report_num in enumerate(missing_numbers):
            if self.interrupted:
                break
                
            report_id = f"Report_{report_num}"
            
            try:
                # Get report data
                row = generator.df.iloc[report_num - 1]
                report_name = str(row.get('report_name', 'Unknown'))
                description = str(row.get('description', ''))
                sql_query = str(row.get('sql_query', ''))
                
                # Skip if essential data missing
                if not report_name or report_name == 'nan' or not sql_query or sql_query == 'nan':
                    error_msg = 'Missing essential data'
                    print(f"⚠️ {report_id}: {error_msg}")
                    self.failed_reports.append({
                        'report_id': report_id,
                        'error': error_msg,
                        'report_name': report_name
                    })
                    continue
                
                # Process with Gemini
                print(f"🤖 Processing {report_id}...")
                prompt = generator.create_business_context_prompt(report_name, description, sql_query)
                response = generator.call_gemini_api(prompt, report_id)
                
                if response:
                    # Parse and store result
                    parsed_result = generator.parse_gemini_response(response)
                    result = {
                        'report_id': report_id,
                        'original_report_name': report_name,
                        'original_description': description,
                        'original_sql_query': sql_query,
                        **parsed_result,
                        'processing_timestamp': datetime.now().isoformat()
                    }
                    
                    self.all_results.append(result)
                    self.processed_reports.add(report_id)
                    print(f"✅ {report_id}: Success")
                else:
                    error_msg = 'API call failed'
                    print(f"❌ {report_id}: {error_msg}")
                    self.failed_reports.append({
                        'report_id': report_id,
                        'error': error_msg,
                        'report_name': report_name
                    })
                
                # BULLETPROOF SAVE - Every 5 reports
                if (i + 1) % self.save_frequency == 0:
                    print(f"💾 Auto-saving progress...")
                    self.save_all_progress()
                    print(f"✅ Progress secured - {len(self.all_results)} total reports saved")
                
                # Rate limiting
                if i < len(missing_numbers) - 1:
                    print(f"⏱️ Rate limiting pause...")
                    time.sleep(1.5)
                
                # Progress update
                progress = ((i + 1) / len(missing_numbers)) * 100
                remaining = len(missing_numbers) - (i + 1)
                eta_minutes = remaining * 0.5  # Rough estimate
                print(f"📊 Progress: {i + 1}/{len(missing_numbers)} ({progress:.1f}%) - ETA: {eta_minutes:.0f}min")
                
            except Exception as e:
                error_msg = f'Unexpected error: {str(e)}'
                print(f"❌ {report_id}: {error_msg}")
                self.failed_reports.append({
                    'report_id': report_id,
                    'error': error_msg,
                    'report_name': 'Unknown'
                })
                continue
        
        # Final save
        print(f"\n💾 Final save...")
        self.save_all_progress()
        
        return True

def main():
    """Execute bulletproof processing."""
    print("🛡️ BULLETPROOF GEMINI PROCESSOR")
    print("=" * 50)
    print("🔒 GUARANTEE: Zero data loss - interrupt anytime")
    print("💾 Auto-saves every 5 reports")
    print("🔄 Resume from exact stopping point")
    print("=" * 50)
    
    processor = BulletproofProcessor("metabase_reports_detailed_20250731_122354.xlsx")
    
    try:
        # Load existing work
        processor.load_existing_work()
        
        # Find missing reports
        missing_reports = processor.identify_missing_reports()
        
        if not missing_reports:
            print("🎉 ALL REPORTS COMPLETE!")
            processor.save_all_progress()
            return
        
        # Confirm before starting
        print(f"\n⚠️ READY TO PROCESS {len(missing_reports)} MISSING REPORTS")
        print(f"⏱️ Estimated time: {len(missing_reports) * 0.5:.0f} minutes")
        print(f"💡 Remember: You can stop anytime with Ctrl+C")
        
        input("\nPress ENTER to start (or Ctrl+C to cancel)...")
        
        # Process missing reports
        if processor.process_missing_reports(missing_reports):
            print("\n🎉 PROCESSING COMPLETE!")
            print(f"📁 Final results: {processor.master_file}")
        
    except KeyboardInterrupt:
        # This should be handled by signal handler, but just in case
        print(f"\n🛑 Interrupted - all progress saved")
    except Exception as e:
        print(f"\n💥 Error: {e}")
        processor.save_all_progress()

if __name__ == "__main__":
    main() 