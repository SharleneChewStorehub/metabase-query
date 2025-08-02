#!/usr/bin/env python3
"""
Gemini Business Context Generator - Safe Sequential Version

This script processes Metabase reports from an Excel file and generates
structured business context summaries using Google's Gemini 2.5 Pro model.
Designed for safe, sequential processing with robust rate limiting.

Author: Business Intelligence Team
Date: January 2025
"""

import pandas as pd
import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import warnings
from dotenv import load_dotenv

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning)

class GeminiBusinessContextGenerator:
    """
    Generates structured business context for Metabase reports using Gemini 2.5 Pro.
    Safe sequential processing with robust rate limiting and error handling.
    """
    
    def __init__(self, excel_file_path: str):
        """
        Initialize the generator.
        
        Args:
            excel_file_path (str): Path to the Excel file containing report data
        """
        self.excel_file_path = Path(excel_file_path)
        self.df = None
        self.results = []
        self.failed_reports = []
        
        # CRITICAL: Safe rate limiting - 1.5 seconds minimum between API calls
        self.request_delay = 1.5  # seconds between requests (required for API rate limit)
        
        # Configure logging
        self.setup_logging()
        
        # Validate file exists
        if not self.excel_file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_file_path}")
    
    def setup_logging(self) -> None:
        """Configure logging for the application."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('gemini_business_context.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_gemini_api(self) -> bool:
        """
        Setup Gemini API with secure key management from .env file.
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            # Load environment variables from .env files
            load_dotenv('gemini_config.env')
            load_dotenv('.env')  # Also check standard .env file
            
            # Try to get API key from environment variable
            api_key = os.getenv('GEMINI_API_KEY')
            
            if not api_key or api_key == 'your-api-key-here':
                self.logger.error("🔑 Gemini API key not found or not configured.")
                print("\n❌ CRITICAL: Gemini API key not configured!")
                print("Please update your API key in one of these files:")
                print("  1. gemini_config.env - Replace 'your-api-key-here' with your actual key")
                print("  2. .env - Add line: GEMINI_API_KEY=your-actual-key-here")
                print("  3. Get your key from: https://aistudio.google.com/app/apikey")
                return False
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Initialize the model (Gemini 2.5 Pro for highest quality)
            generation_config = {
                "temperature": 0.1,  # Low temperature for consistent, structured output
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            self.model = genai.GenerativeModel(
                model_name="gemini-2.5-pro",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            self.logger.info("✅ Gemini 2.5 Pro model initialized successfully")
            print("🤖 Gemini 2.5 Pro API configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup Gemini API: {str(e)}")
            print(f"❌ API setup failed: {str(e)}")
            return False
    
    def load_excel_data(self) -> bool:
        """
        Load data from the Excel file.
        
        Returns:
            bool: True if loading successful, False otherwise
        """
        try:
            self.logger.info(f"📖 Loading Excel file: {self.excel_file_path}")
            print(f"📖 Loading Excel file: {self.excel_file_path}")
            
            # Read the Excel file - assuming data is in the first sheet
            self.df = pd.read_excel(self.excel_file_path, engine='openpyxl')
            
            self.logger.info(f"✅ Loaded {len(self.df)} reports from Excel file")
            print(f"✅ Loaded {len(self.df)} reports from Excel file")
            self.logger.info(f"📋 Columns: {list(self.df.columns)}")
            
            # Validate required columns exist
            required_columns = ['report_name', 'description', 'sql_query']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            
            if missing_columns:
                self.logger.error(f"❌ Missing required columns: {missing_columns}")
                print(f"❌ Missing required columns: {missing_columns}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load Excel file: {str(e)}")
            print(f"❌ Failed to load Excel file: {str(e)}")
            return False
    
    def create_business_context_prompt(self, report_name: str, description: str, sql_query: str) -> str:
        """
        Create the refined 'Deconstruction-then-Synthesis' prompt for Gemini API.
        
        Args:
            report_name (str): Name of the report
            description (str): Report description
            sql_query (str): SQL query for the report
            
        Returns:
            str: Formatted prompt for Gemini
        """
        prompt = f"""You are an expert business analyst who is also an expert at reading SQL. I will provide a 'Report Name', its 'Description', and its 'SQL Query'.

Your task is to generate a structured business summary by following these three steps:
1. **Deconstruct the SQL:** From the `SELECT` and `WHERE` clauses, identify the primary **Metrics** and all key **Business Filters**.
2. **Synthesize the Context:** Use the `Report Name` and `Description` as the primary context, then combine it with the extracted Metrics and Filters to formulate the specific **Business Question** the query answers.
3. **Generate the Final Output:** Create a summary in the following structured Markdown format. Adhere to this format exactly.

---
**Business Question:** [Your synthesized question here]
**Primary Metric(s):**
- [Metric 1]
- [Metric 2]
**Key Filters / Levers:**
- [Filter 1]
- [Filter 2]
**Final Summary:** [A concise, 1-2 sentence summary synthesizing everything.]
---

**Input Data:**
Report Name: {report_name}
Description: {description if description and str(description).strip() != 'nan' else 'Not provided'}
SQL Query: 
{sql_query}

Please generate the structured business summary now:"""
        
        return prompt
    
    def call_gemini_api(self, prompt: str, report_id: str) -> Optional[str]:
        """
        Make a call to Gemini API with comprehensive error handling.
        
        Args:
            prompt (str): The prompt to send to Gemini
            report_id (str): Identifier for the report (for logging)
            
        Returns:
            Optional[str]: Generated response or None if failed
        """
        try:
            self.logger.info(f"🤖 Processing {report_id} with Gemini 2.5 Pro...")
            print(f"🤖 Processing {report_id}...")
            
            # Make the API call
            response = self.model.generate_content(prompt)
            
            # Check if response was blocked
            if response.candidates and response.candidates[0].finish_reason.name == "SAFETY":
                error_msg = f"Content blocked by safety filters"
                self.logger.warning(f"⚠️ {report_id}: {error_msg}")
                print(f"⚠️ {report_id}: {error_msg}")
                return None
            
            # Extract text from response
            if response.text:
                self.logger.info(f"✅ {report_id}: Successfully generated business context")
                print(f"✅ {report_id}: Success")
                return response.text.strip()
            else:
                error_msg = f"Empty response from Gemini"
                self.logger.warning(f"⚠️ {report_id}: {error_msg}")
                print(f"⚠️ {report_id}: {error_msg}")
                return None
                
        except Exception as e:
            error_msg = f"API call failed - {str(e)}"
            self.logger.error(f"❌ {report_id}: {error_msg}")
            print(f"❌ {report_id}: {error_msg}")
            return None
    
    def parse_gemini_response(self, response_text: str) -> Dict[str, str]:
        """
        Parse the structured response from Gemini.
        
        Args:
            response_text (str): Raw response from Gemini
            
        Returns:
            Dict[str, str]: Parsed components
        """
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
                
                if line.startswith('**Business Question:**'):
                    result['business_question'] = line.replace('**Business Question:**', '').strip()
                elif line.startswith('**Primary Metric(s):**'):
                    current_section = 'metrics'
                elif line.startswith('**Key Filters / Levers:**'):
                    current_section = 'filters'
                elif line.startswith('**Final Summary:**'):
                    result['final_summary'] = line.replace('**Final Summary:**', '').strip()
                    current_section = None
                elif line.startswith('- ') and current_section:
                    metric_or_filter = line[2:].strip()
                    if current_section == 'metrics':
                        if result['primary_metrics']:
                            result['primary_metrics'] += '\n' + metric_or_filter
                        else:
                            result['primary_metrics'] = metric_or_filter
                    elif current_section == 'filters':
                        if result['key_filters']:
                            result['key_filters'] += '\n' + metric_or_filter
                        else:
                            result['key_filters'] = metric_or_filter
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to parse Gemini response: {str(e)}")
            # If parsing fails, store the raw response
            result['business_question'] = 'Parsing failed - see raw response'
        
        return result
    
    def process_reports(self, start_from_report: int = 1, end_at_report: int = None) -> bool:
        """
        Process all reports sequentially with strict rate limiting.
        CRITICAL: One-by-one processing with mandatory delays.
        
        Args:
            start_from_report (int): Report number to start from (1-based index)
            end_at_report (int): Report number to end at (1-based index, inclusive). If None, process to end.
        
        Returns:
            bool: True if processing completed, False if setup failed
        """
        if self.df is None:
            self.logger.error("❌ No data loaded. Call load_excel_data() first.")
            print("❌ No data loaded. Please check Excel file loading.")
            return False
        
        total_reports = len(self.df)
        start_index = start_from_report - 1  # Convert to 0-based index
        end_index = (end_at_report - 1) if end_at_report else (total_reports - 1)  # Convert to 0-based index
        
        processing_count = end_index - start_index + 1
        
        if start_from_report > 1 or end_at_report:
            range_desc = f"Report_{start_from_report} to Report_{end_at_report or total_reports}"
            self.logger.info(f"🔄 PROCESSING range {range_desc} ({processing_count} reports)...")
            print(f"\n🔄 PROCESSING RANGE: {range_desc}")
            print(f"📊 Reports to process: {processing_count}")
        else:
            self.logger.info(f"🚀 Starting SEQUENTIAL processing of {total_reports} reports...")
            print(f"\n🚀 Starting SEQUENTIAL processing of {total_reports} reports...")
        
        print(f"⏱️  Rate limiting: {self.request_delay}s pause after EVERY API call")
        print("=" * 60)
        
        # Sequential processing loop - ONE BY ONE, for specified range
        for index in range(start_index, end_index + 1):
            row = self.df.iloc[index]
            report_id = f"Report_{index + 1}"
            
            try:
                # Extract data from row
                report_name = str(row.get('report_name', 'Unknown'))
                description = str(row.get('description', ''))
                sql_query = str(row.get('sql_query', ''))
                
                # Skip if essential data is missing
                if not report_name or report_name == 'nan' or not sql_query or sql_query == 'nan':
                    error_msg = 'Missing essential data (name or SQL)'
                    self.logger.warning(f"⚠️ {report_id}: Skipping - {error_msg}")
                    print(f"⚠️ {report_id}: Skipping - {error_msg}")
                    
                    self.failed_reports.append({
                        'report_id': report_id,
                        'error': error_msg,
                        'report_name': report_name
                    })
                    continue
                
                # Create the refined prompt
                prompt = self.create_business_context_prompt(report_name, description, sql_query)
                
                # Call Gemini API
                response = self.call_gemini_api(prompt, report_id)
                
                if response:
                    # Parse response
                    parsed_result = self.parse_gemini_response(response)
                    
                    # Add original data
                    result = {
                        'report_id': report_id,
                        'original_report_name': report_name,
                        'original_description': description,
                        'original_sql_query': sql_query,
                        **parsed_result,
                        'processing_timestamp': datetime.now().isoformat()
                    }
                    
                    self.results.append(result)
                    
                else:
                    error_msg = 'API call failed or content blocked'
                    self.failed_reports.append({
                        'report_id': report_id,
                        'error': error_msg,
                        'report_name': report_name
                    })
                
                # CRITICAL: Mandatory rate limiting pause after EVERY API call
                # This ensures we stay well under the 60 RPM limit
                if index < end_index:  # Don't pause after the last request in range
                    self.logger.info(f"⏱️  Mandatory {self.request_delay}s pause for rate limiting...")
                    print(f"⏱️  Pausing {self.request_delay}s...")
                    time.sleep(self.request_delay)
                
                # Progress update
                range_progress = ((index - start_index + 1) / processing_count) * 100
                completed_in_session = len(self.results)
                self.logger.info(f"📊 Progress: {index + 1}/{total_reports} (Range: {range_progress:.1f}%) - Session: {completed_in_session}")
                print(f"📊 Progress: {index + 1}/{total_reports} (Range: {range_progress:.1f}%) - Session: {completed_in_session}")
                
                # Save incremental progress every 25 reports to prevent loss
                if completed_in_session > 0 and completed_in_session % 25 == 0:
                    print(f"💾 Saving incremental progress after {completed_in_session} reports...")
                    temp_file = f"temp_progress_{completed_in_session}_reports.xlsx"
                    self.save_results(temp_file)
                
            except Exception as e:
                error_msg = f'Unexpected error: {str(e)}'
                self.logger.error(f"❌ {report_id}: {error_msg}")
                print(f"❌ {report_id}: {error_msg}")
                
                self.failed_reports.append({
                    'report_id': report_id,
                    'error': error_msg,
                    'report_name': report_name if 'report_name' in locals() else 'Unknown'
                })
                
                # Continue processing despite errors - robust error handling
                continue
        
        print("\n" + "=" * 60)
        completed_in_session = len(self.results)
        total_completed = start_from_report - 1 + completed_in_session
        self.logger.info(f"✅ Processing complete! Successfully processed {completed_in_session} reports in this session")
        self.logger.info(f"📊 Total completed: {total_completed} out of {total_reports} reports")
        print(f"✅ Processing complete! Successfully processed {completed_in_session} reports in this session")
        print(f"📊 Total completed: {total_completed} out of {total_reports} reports")
        
        if self.failed_reports:
            self.logger.warning(f"⚠️ {len(self.failed_reports)} reports failed to process in this session")
            print(f"⚠️ {len(self.failed_reports)} reports failed to process in this session")
        
        return True
    
    def save_results(self, output_file: str = None) -> str:
        """
        Save results to Excel file.
        
        Args:
            output_file (str, optional): Output file path
            
        Returns:
            str: Path to the saved file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"metabase_reports_with_business_context_{timestamp}.xlsx"
        
        try:
            # Create DataFrame from results
            if self.results:
                results_df = pd.DataFrame(self.results)
                
                # Create a summary sheet
                summary_data = {
                    'Metric': [
                        'Total Reports Processed',
                        'Successfully Generated Context',
                        'Failed to Process',
                        'Success Rate (%)',
                        'Processing Date',
                        'Gemini Model Used',
                        'Rate Limiting Delay (seconds)'
                    ],
                    'Value': [
                        len(self.df) if self.df is not None else 0,
                        len(self.results),
                        len(self.failed_reports),
                        f"{(len(self.results) / len(self.df) * 100):.1f}" if self.df is not None and len(self.df) > 0 else "0.0",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Gemini 2.5 Pro",
                        self.request_delay
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                
                # Save to Excel with multiple sheets
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    results_df.to_excel(writer, sheet_name='Business_Context_Results', index=False)
                    summary_df.to_excel(writer, sheet_name='Processing_Summary', index=False)
                    
                    if self.failed_reports:
                        failed_df = pd.DataFrame(self.failed_reports)
                        failed_df.to_excel(writer, sheet_name='Failed_Reports', index=False)
                
                self.logger.info(f"💾 Results saved to: {output_file}")
                print(f"💾 Results saved to: {output_file}")
                return output_file
            else:
                self.logger.warning("⚠️ No results to save!")
                print("⚠️ No results to save!")
                return ""
                
        except Exception as e:
            self.logger.error(f"❌ Failed to save results: {str(e)}")
            print(f"❌ Failed to save results: {str(e)}")
            return ""
    
    def display_summary(self) -> None:
        """Display a comprehensive summary of the processing results."""
        print("\n" + "="*80)
        print("📊 GEMINI BUSINESS CONTEXT GENERATION SUMMARY")
        print("="*80)
        
        total_reports = len(self.df) if self.df is not None else 0
        successful = len(self.results)
        failed = len(self.failed_reports)
        
        print(f"📈 Total Reports: {total_reports}")
        print(f"✅ Successfully Processed: {successful}")
        print(f"❌ Failed to Process: {failed}")
        
        if total_reports > 0:
            success_rate = (successful / total_reports) * 100
            print(f"📊 Success Rate: {success_rate:.1f}%")
        
        print(f"🤖 Model Used: Gemini 2.5 Pro")
        print(f"⏱️  Rate Limiting: {self.request_delay}s between requests")
        print(f"🔄 Processing Method: Sequential (Safe)")
        
        if self.results:
            print(f"\n🎯 Sample Business Context Generated:")
            print("-" * 50)
            sample = self.results[0]
            print(f"Report: {sample['original_report_name']}")
            print(f"Business Question: {sample['business_question']}")
            if len(sample['primary_metrics']) > 100:
                print(f"Primary Metrics: {sample['primary_metrics'][:100]}...")
            else:
                print(f"Primary Metrics: {sample['primary_metrics']}")
        
        if self.failed_reports:
            print(f"\n⚠️ Failed Reports:")
            for report in self.failed_reports[:3]:  # Show first 3 failures
                print(f"  - {report['report_id']}: {report['error']}")
            if len(self.failed_reports) > 3:
                print(f"  ... and {len(self.failed_reports) - 3} more")
        
        print("="*80)


def main():
    """Main execution function with comprehensive setup validation."""
    
    # Configuration
    excel_file = "metabase_reports_detailed_20250731_122354.xlsx"
    
    print("🚀 Gemini Business Context Generator - SAFE SEQUENTIAL VERSION")
    print("=" * 70)
    print("🔒 This version uses safe, sequential processing")
    print("⏱️  Rate limiting: 1.5s pause after every API call")
    print("🎯 High-quality 'Deconstruction-then-Synthesis' prompts")
    print("🔑 Secure credential loading from .env files")
    print("=" * 70)
    
    try:
        # Initialize generator
        print("\n🔧 Initializing generator...")
        generator = GeminiBusinessContextGenerator(excel_file)
        
        # Setup Gemini API with secure credentials
        print("🔑 Setting up Gemini API...")
        if not generator.setup_gemini_api():
            print("\n❌ API setup failed. Please configure your Gemini API key.")
            print("📝 Quick setup instructions:")
            print("1. Get your API key from: https://aistudio.google.com/app/apikey")
            print("2. Edit 'gemini_config.env' and replace 'your-api-key-here' with your key")
            print("   OR create/edit '.env' file and add: GEMINI_API_KEY=your-actual-key")
            print("3. Re-run this script")
            return
        
        # Load Excel data
        print("📖 Loading Excel data...")
        if not generator.load_excel_data():
            print("❌ Failed to load Excel data. Please check the file path and format.")
            return
        
        # Confirm processing start
        print(f"\n🎯 Configuration Summary:")
        print(f"   • Model: Gemini 2.5 Pro (highest quality)")
        print(f"   • Rate limiting: {generator.request_delay}s between requests")
        print(f"   • Processing method: Sequential (safe)")
        print(f"   • Total reports: {len(generator.df)}")
        
        # Process reports with safe sequential method
        if generator.process_reports(): # Start from beginning by default
            # Save results
            print("\n💾 Saving results...")
            output_file = generator.save_results()
            
            # Display comprehensive summary
            generator.display_summary()
            
            if output_file:
                print(f"\n📋 Output file contains:")
                print("  • Business_Context_Results: Main results with generated context")
                print("  • Processing_Summary: Overview of processing statistics")
                print("  • Failed_Reports: Details of any failed processing")
        
        print("\n✨ Safe sequential processing complete!")
        
    except KeyboardInterrupt:
        print("\n🛑 Processing interrupted by user")
        print("Note: Any completed results have been saved.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        logging.error(f"Unexpected error in main: {str(e)}")
        print("Check the log file 'gemini_business_context.log' for details.")


if __name__ == "__main__":
    main() 