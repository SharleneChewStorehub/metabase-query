#!/usr/bin/env python3
"""
BULLETPROOF RECOVERY SCRIPT - NEVER LOSE WORK AGAIN

This script implements fail-safe recovery mechanisms to ensure no processed
reports are ever lost due to session interruptions or script failures.
"""

import pandas as pd
import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
from gemini_business_context_generator import GeminiBusinessContextGenerator

class BulletproofRecovery:
    """Fail-safe recovery system that never loses processed work."""
    
    def __init__(self, excel_file: str):
        self.excel_file = excel_file
        self.recovery_file = "RECOVERY_STATE.json"
        self.master_results_file = "MASTER_RESULTS.xlsx"
        self.processed_reports: Set[str] = set()
        self.failed_reports: List[Dict] = []
        self.all_results: List[Dict] = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bulletproof_recovery.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_existing_work(self) -> None:
        """Load ALL existing work from any previous processing."""
        print("🔍 SCANNING FOR EXISTING WORK...")
        
        # 1. Load from master results file if it exists
        if os.path.exists(self.master_results_file):
            try:
                df = pd.read_excel(self.master_results_file, sheet_name='Business_Context_Results')
                for _, row in df.iterrows():
                    report_id = row.get('report_id', '')
                    if report_id:
                        self.processed_reports.add(report_id)
                        self.all_results.append(row.to_dict())
                print(f"✅ Loaded {len(df)} reports from master results file")
            except Exception as e:
                print(f"⚠️ Could not load master results: {e}")
        
        # 2. Load from all existing progress files
        import glob
        progress_files = glob.glob("temp_progress_*.xlsx") + glob.glob("*business_context*.xlsx")
        
        for file_path in progress_files:
            if file_path == self.master_results_file:
                continue  # Already processed
                
            try:
                df = pd.read_excel(file_path, sheet_name='Business_Context_Results')
                new_count = 0
                for _, row in df.iterrows():
                    report_id = row.get('report_id', '')
                    if report_id and report_id not in self.processed_reports:
                        self.processed_reports.add(report_id)
                        self.all_results.append(row.to_dict())
                        new_count += 1
                if new_count > 0:
                    print(f"✅ Recovered {new_count} additional reports from {file_path}")
            except Exception as e:
                print(f"⚠️ Could not load {file_path}: {e}")
        
        # 3. Load recovery state
        if os.path.exists(self.recovery_file):
            try:
                with open(self.recovery_file, 'r') as f:
                    recovery_data = json.load(f)
                    self.failed_reports = recovery_data.get('failed_reports', [])
                print(f"✅ Loaded recovery state with {len(self.failed_reports)} known failures")
            except Exception as e:
                print(f"⚠️ Could not load recovery state: {e}")
        
        print(f"📊 RECOVERY SUMMARY:")
        print(f"   • Total recovered reports: {len(self.processed_reports)}")
        print(f"   • Known failed reports: {len(self.failed_reports)}")
    
    def identify_missing_reports(self) -> List[int]:
        """Identify which reports still need processing."""
        # Load original dataset to know total reports
        df_original = pd.read_excel(self.excel_file)
        total_reports = len(df_original)
        
        # Find missing report numbers
        all_report_numbers = set(range(1, total_reports + 1))
        processed_numbers = set()
        
        for report_id in self.processed_reports:
            try:
                num = int(report_id.replace('Report_', ''))
                processed_numbers.add(num)
            except:
                continue
        
        missing_numbers = sorted(all_report_numbers - processed_numbers)
        
        print(f"📊 MISSING REPORTS ANALYSIS:")
        print(f"   • Total reports in dataset: {total_reports}")
        print(f"   • Successfully processed: {len(processed_numbers)}")
        print(f"   • Still missing: {len(missing_numbers)}")
        print(f"   • Completion rate: {(len(processed_numbers)/total_reports)*100:.1f}%")
        
        if missing_numbers:
            print(f"   • Missing ranges: {self._format_ranges(missing_numbers)}")
        
        return missing_numbers
    
    def _format_ranges(self, numbers: List[int]) -> str:
        """Format list of numbers into ranges for display."""
        if not numbers:
            return "None"
        
        ranges = []
        start = numbers[0]
        end = numbers[0]
        
        for num in numbers[1:] + [None]:  # Add None to close last range
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
    
    def save_master_results(self) -> str:
        """Save all results to master file with bulletproof error handling."""
        if not self.all_results:
            print("⚠️ No results to save")
            return ""
        
        # Sort results by report number
        def extract_number(result):
            try:
                return int(result['report_id'].replace('Report_', ''))
            except:
                return 0
        
        self.all_results.sort(key=extract_number)
        
        # Create DataFrames
        results_df = pd.DataFrame(self.all_results)
        
        # Create comprehensive summary
        total_in_dataset = len(pd.read_excel(self.excel_file))
        summary_data = {
            'Metric': [
                'Total Reports in Dataset',
                'Successfully Processed',
                'Failed to Process',
                'Completion Rate (%)',
                'Last Updated',
                'Processing Method',
                'Recovery System'
            ],
            'Value': [
                total_in_dataset,
                len(self.all_results),
                len(self.failed_reports),
                f"{(len(self.all_results)/total_in_dataset)*100:.1f}",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Bulletproof Recovery",
                "Fail-safe Active"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        # Save with atomic operation
        temp_file = f"{self.master_results_file}.tmp"
        try:
            with pd.ExcelWriter(temp_file, engine='openpyxl') as writer:
                results_df.to_excel(writer, sheet_name='Business_Context_Results', index=False)
                summary_df.to_excel(writer, sheet_name='Processing_Summary', index=False)
                
                if self.failed_reports:
                    failed_df = pd.DataFrame(self.failed_reports)
                    failed_df.to_excel(writer, sheet_name='Failed_Reports', index=False)
            
            # Atomic rename (prevents corruption)
            os.rename(temp_file, self.master_results_file)
            print(f"💾 Master results saved: {self.master_results_file}")
            return self.master_results_file
            
        except Exception as e:
            print(f"❌ Failed to save master results: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return ""
    
    def save_recovery_state(self) -> None:
        """Save recovery state for bulletproof resumption."""
        recovery_data = {
            'processed_reports': list(self.processed_reports),
            'failed_reports': self.failed_reports,
            'last_update': datetime.now().isoformat()
        }
        
        temp_file = f"{self.recovery_file}.tmp"
        try:
            with open(temp_file, 'w') as f:
                json.dump(recovery_data, f, indent=2)
            os.rename(temp_file, self.recovery_file)
            self.logger.info("💾 Recovery state saved")
        except Exception as e:
            self.logger.error(f"❌ Failed to save recovery state: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def process_missing_reports(self, missing_numbers: List[int]) -> bool:
        """Process only the missing reports with bulletproof error handling."""
        if not missing_numbers:
            print("✅ No missing reports to process!")
            return True
        
        print(f"\n🚀 PROCESSING {len(missing_numbers)} MISSING REPORTS...")
        print(f"⏱️ Estimated time: {len(missing_numbers) * 0.5:.0f} minutes")
        
        # Initialize generator
        generator = GeminiBusinessContextGenerator(self.excel_file)
        
        if not generator.setup_gemini_api():
            print("❌ API setup failed")
            return False
        
        if not generator.load_excel_data():
            print("❌ Data loading failed")
            return False
        
        # Process each missing report
        for i, report_num in enumerate(missing_numbers):
            report_id = f"Report_{report_num}"
            
            try:
                # Get report data
                row = generator.df.iloc[report_num - 1]  # Convert to 0-based index
                report_name = str(row.get('report_name', 'Unknown'))
                description = str(row.get('description', ''))
                sql_query = str(row.get('sql_query', ''))
                
                if not report_name or report_name == 'nan' or not sql_query or sql_query == 'nan':
                    error_msg = 'Missing essential data'
                    print(f"⚠️ {report_id}: {error_msg}")
                    self.failed_reports.append({
                        'report_id': report_id,
                        'error': error_msg,
                        'report_name': report_name
                    })
                    continue
                
                # Create prompt and call API
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
                
                # Save progress every 10 reports (bulletproof backup)
                if (i + 1) % 10 == 0:
                    self.save_master_results()
                    self.save_recovery_state()
                    print(f"💾 Progress saved after {i + 1} reports")
                
                # Rate limiting
                if i < len(missing_numbers) - 1:
                    time.sleep(1.5)
                
                # Progress update
                progress = ((i + 1) / len(missing_numbers)) * 100
                print(f"📊 Progress: {i + 1}/{len(missing_numbers)} ({progress:.1f}%)")
                
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
        self.save_master_results()
        self.save_recovery_state()
        
        return True

def main():
    """Execute bulletproof recovery process."""
    print("🛡️ BULLETPROOF RECOVERY SYSTEM")
    print("=" * 50)
    print("🎯 Mission: Recover ALL work and complete processing")
    print("🔒 Guarantee: NO work will be lost")
    print("=" * 50)
    
    recovery = BulletproofRecovery("metabase_reports_detailed_20250731_122354.xlsx")
    
    try:
        # Step 1: Load all existing work
        recovery.load_existing_work()
        
        # Step 2: Identify what's missing
        missing_reports = recovery.identify_missing_reports()
        
        if not missing_reports:
            print("🎉 ALL REPORTS ALREADY PROCESSED!")
            recovery.save_master_results()
            return
        
        # Step 3: Process only missing reports
        print(f"\n⚠️ FOUND {len(missing_reports)} MISSING REPORTS")
        print(f"🎯 Processing ONLY missing reports to minimize time")
        
        if recovery.process_missing_reports(missing_reports):
            print("\n🎉 RECOVERY COMPLETE!")
            final_file = recovery.save_master_results()
            print(f"📁 Final complete file: {final_file}")
        else:
            print("\n❌ Recovery failed")
    
    except Exception as e:
        print(f"\n💥 Critical error: {e}")
        recovery.save_recovery_state()  # Save state even on failure

if __name__ == "__main__":
    main() 