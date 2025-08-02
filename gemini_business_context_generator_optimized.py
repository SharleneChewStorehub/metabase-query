#!/usr/bin/env python3
"""
Gemini Business Context Generator - Optimized Version

High-performance version with concurrent processing, intelligent batching,
and optimized rate limiting for faster processing of large datasets.

Author: Business Intelligence Team
Date: January 2025
"""

import pandas as pd
import os
import time
import json
import logging
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import warnings
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning)

class OptimizedGeminiProcessor:
    """
    High-performance Gemini processor with concurrent processing and intelligent rate limiting.
    """
    
    def __init__(self, excel_file_path: str, max_workers: int = 5):
        """
        Initialize the optimized processor.
        
        Args:
            excel_file_path (str): Path to the Excel file
            max_workers (int): Number of concurrent workers (default: 5 for 60 RPM)
        """
        self.excel_file_path = Path(excel_file_path)
        self.df = None
        self.results = []
        self.failed_reports = []
        self.max_workers = max_workers
        
        # Optimized rate limiting (60 RPM = 1 request per second, with 5 workers = 0.2s interval)
        self.rate_limit_interval = 1.0 / (60 / max_workers)  # Dynamic based on workers
        self.request_queue = Queue()
        self.rate_limiter_lock = threading.Lock()
        self.last_request_time = 0
        
        # Performance tracking
        self.start_time = None
        self.processed_count = 0
        
        # Setup logging
        self.setup_logging()
        
        if not self.excel_file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_file_path}")
    
    def setup_logging(self) -> None:
        """Configure logging for the application."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('gemini_optimized.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_gemini_api(self) -> bool:
        """Setup Gemini API with optimized configuration."""
        try:
            load_dotenv('gemini_config.env')
            api_key = os.getenv('GEMINI_API_KEY')
            
            if not api_key or api_key == 'your-api-key-here':
                print("🔑 Please configure your API key in 'gemini_config.env'")
                return False
            
            genai.configure(api_key=api_key)
            
            # Optimized generation config for faster processing
            generation_config = {
                "temperature": float(os.getenv('GEMINI_TEMPERATURE', 0.1)),
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": int(os.getenv('GEMINI_MAX_TOKENS', 1500)),  # Reduced for speed
            }
            
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro')
            self.model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            self.logger.info(f"✅ {model_name} initialized with {self.max_workers} workers")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup Gemini API: {str(e)}")
            return False
    
    def load_excel_data(self) -> bool:
        """Load and validate Excel data."""
        try:
            self.logger.info(f"📖 Loading Excel file: {self.excel_file_path}")
            self.df = pd.read_excel(self.excel_file_path, engine='openpyxl')
            
            required_columns = ['report_name', 'description', 'sql_query']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            
            if missing_columns:
                self.logger.error(f"❌ Missing columns: {missing_columns}")
                return False
            
            self.logger.info(f"✅ Loaded {len(self.df)} reports")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load Excel: {str(e)}")
            return False
    
    def create_optimized_prompt(self, report_name: str, description: str, sql_query: str) -> str:
        """Create a more concise prompt for faster processing."""
        prompt = f"""Generate structured business context for this Metabase report. Follow this EXACT format:

**Business Question:** [What specific business question does this answer?]
**Primary Metric(s):**
- [Key metric 1]
- [Key metric 2]
**Key Filters / Levers:**
- [Business filter 1]
- [Business filter 2]  
**Final Summary:** [1-2 sentence business summary]

Input:
Report: {report_name}
Description: {description if description and str(description).strip() != 'nan' else 'Not provided'}
SQL: {sql_query[:2000]}{'...' if len(sql_query) > 2000 else ''}

Generate the structured context:"""
        return prompt
    
    def rate_limited_api_call(self, prompt: str, report_id: str) -> Optional[str]:
        """Make rate-limited API call with intelligent timing."""
        with self.rate_limiter_lock:
            # Calculate wait time
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.rate_limit_interval:
                wait_time = self.rate_limit_interval - time_since_last
                time.sleep(wait_time)
            
            self.last_request_time = time.time()
        
        try:
            response = self.model.generate_content(prompt)
            
            if response.candidates and response.candidates[0].finish_reason.name == "SAFETY":
                self.logger.warning(f"⚠️ {report_id}: Content blocked")
                return None
            
            return response.text.strip() if response.text else None
            
        except Exception as e:
            self.logger.error(f"❌ {report_id}: API error - {str(e)}")
            return None
    
    def process_single_report(self, row_data: tuple) -> Dict:
        """Process a single report with error handling."""
        index, row = row_data
        report_id = f"Report_{index + 1}"
        
        try:
            # Extract data
            report_name = str(row.get('report_name', 'Unknown'))
            description = str(row.get('description', ''))
            sql_query = str(row.get('sql_query', ''))
            
            # Skip invalid data
            if not report_name or report_name == 'nan' or not sql_query or sql_query == 'nan':
                return {
                    'status': 'failed',
                    'report_id': report_id,
                    'error': 'Missing essential data',
                    'report_name': report_name
                }
            
            # Create prompt and call API
            prompt = self.create_optimized_prompt(report_name, description, sql_query)
            response = self.rate_limited_api_call(prompt, report_id)
            
            if response:
                parsed = self.parse_gemini_response(response)
                
                with self.rate_limiter_lock:
                    self.processed_count += 1
                    if self.processed_count % 50 == 0:  # Progress every 50 reports
                        elapsed = time.time() - self.start_time
                        rate = self.processed_count / elapsed * 60  # Reports per minute
                        remaining = len(self.df) - self.processed_count
                        eta = remaining / (rate / 60) if rate > 0 else 0
                        self.logger.info(f"🚀 Processed {self.processed_count}/{len(self.df)} | Rate: {rate:.1f}/min | ETA: {eta/60:.1f}min")
                
                return {
                    'status': 'success',
                    'report_id': report_id,
                    'original_report_name': report_name,
                    'original_description': description,
                    'original_sql_query': sql_query,
                    **parsed,
                    'processing_timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'failed',
                    'report_id': report_id,
                    'error': 'API call failed',
                    'report_name': report_name
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'report_id': report_id,
                'error': f'Unexpected error: {str(e)}',
                'report_name': report_name if 'report_name' in locals() else 'Unknown'
            }
    
    def parse_gemini_response(self, response_text: str) -> Dict[str, str]:
        """Parse Gemini response efficiently."""
        result = {
            'business_question': '',
            'primary_metrics': '',
            'key_filters': '',
            'final_summary': '',
            'raw_response': response_text
        }
        
        try:
            lines = response_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if '**Business Question:**' in line:
                    result['business_question'] = line.split('**Business Question:**')[-1].strip()
                elif '**Primary Metric(s):**' in line:
                    current_section = 'metrics'
                elif '**Key Filters' in line:
                    current_section = 'filters'
                elif '**Final Summary:**' in line:
                    result['final_summary'] = line.split('**Final Summary:**')[-1].strip()
                    current_section = None
                elif line.startswith('- ') and current_section:
                    content = line[2:].strip()
                    if current_section == 'metrics':
                        result['primary_metrics'] += content + '\n'
                    elif current_section == 'filters':
                        result['key_filters'] += content + '\n'
        except:
            result['business_question'] = 'Parsing failed - see raw response'
        
        # Clean up
        result['primary_metrics'] = result['primary_metrics'].strip()
        result['key_filters'] = result['key_filters'].strip()
        
        return result
    
    def process_reports_concurrent(self) -> bool:
        """Process reports using concurrent workers."""
        if self.df is None:
            return False
        
        total_reports = len(self.df)
        self.start_time = time.time()
        
        self.logger.info(f"🚀 Starting concurrent processing: {total_reports} reports with {self.max_workers} workers")
        self.logger.info(f"⚡ Estimated time: {(total_reports * self.rate_limit_interval) / 60:.1f} minutes")
        
        # Prepare data for processing
        report_data = [(index, row) for index, row in self.df.iterrows()]
        
        # Process with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_report = {
                executor.submit(self.process_single_report, data): data[0] 
                for data in report_data
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_report):
                result = future.result()
                
                if result['status'] == 'success':
                    self.results.append(result)
                else:
                    self.failed_reports.append({
                        'report_id': result['report_id'],
                        'error': result['error'],
                        'report_name': result['report_name']
                    })
        
        elapsed = time.time() - self.start_time
        success_rate = len(self.results) / total_reports * 100
        
        self.logger.info(f"✅ Processing complete!")
        self.logger.info(f"⏱️  Total time: {elapsed/60:.1f} minutes")
        self.logger.info(f"📊 Success rate: {success_rate:.1f}% ({len(self.results)}/{total_reports})")
        self.logger.info(f"🚀 Processing rate: {total_reports/(elapsed/60):.1f} reports/minute")
        
        return True
    
    def save_results(self, output_file: str = None) -> str:
        """Save results to Excel file."""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"metabase_business_context_optimized_{timestamp}.xlsx"
        
        try:
            if self.results:
                results_df = pd.DataFrame(self.results)
                
                # Performance summary
                elapsed = time.time() - self.start_time if self.start_time else 0
                summary_data = {
                    'Metric': [
                        'Total Reports',
                        'Successfully Processed',
                        'Failed',
                        'Success Rate (%)',
                        'Processing Time (minutes)',
                        'Reports per Minute',
                        'Model Used',
                        'Concurrent Workers'
                    ],
                    'Value': [
                        len(self.df),
                        len(self.results),
                        len(self.failed_reports),
                        f"{(len(self.results) / len(self.df) * 100):.1f}",
                        f"{elapsed/60:.1f}",
                        f"{len(self.df)/(elapsed/60):.1f}" if elapsed > 0 else "N/A",
                        os.getenv('GEMINI_MODEL', 'gemini-2.5-pro'),
                        str(self.max_workers)
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    results_df.to_excel(writer, sheet_name='Business_Context_Results', index=False)
                    summary_df.to_excel(writer, sheet_name='Performance_Summary', index=False)
                    
                    if self.failed_reports:
                        failed_df = pd.DataFrame(self.failed_reports)
                        failed_df.to_excel(writer, sheet_name='Failed_Reports', index=False)
                
                self.logger.info(f"💾 Results saved to: {output_file}")
                return output_file
            
            return ""
        except Exception as e:
            self.logger.error(f"❌ Save failed: {str(e)}")
            return ""


def main():
    """Main execution with performance optimization."""
    excel_file = "metabase_reports_detailed_20250731_122354.xlsx"
    
    print("🚀 Optimized Gemini Business Context Generator")
    print("=" * 60)
    
    try:
        # Initialize with optimized settings
        max_workers = 5  # Optimal for 60 RPM limit
        processor = OptimizedGeminiProcessor(excel_file, max_workers)
        
        if not processor.setup_gemini_api():
            print("❌ API setup failed. Configure gemini_config.env")
            return
        
        if not processor.load_excel_data():
            print("❌ Failed to load Excel data")
            return
        
        # Show performance estimate
        total_reports = len(processor.df)
        estimated_time = (total_reports * processor.rate_limit_interval) / 60
        
        print(f"📊 Processing {total_reports} reports")
        print(f"⚡ Using {max_workers} concurrent workers")
        print(f"⏱️  Estimated time: {estimated_time:.1f} minutes")
        print(f"🎯 Expected rate: ~{60 * max_workers} requests/minute")
        
        if processor.process_reports_concurrent():
            output_file = processor.save_results()
            
            if output_file:
                print(f"\n💾 Results saved to: {output_file}")
                print("🎉 Optimized processing complete!")
        
    except KeyboardInterrupt:
        print("\n🛑 Processing interrupted")
    except Exception as e:
        print(f"\n💥 Error: {str(e)}")


if __name__ == "__main__":
    main() 