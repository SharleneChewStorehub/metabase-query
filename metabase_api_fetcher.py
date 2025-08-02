#!/usr/bin/env python3
"""
Metabase API Report Fetcher

A robust Python script to fetch detailed report information from Metabase API
based on Report IDs from an Excel file.

Features:
- Secure configuration management
- Robust error handling and retry logic
- Respectful API rate limiting
- Comprehensive logging
- Data validation and cleaning
"""

import pandas as pd
import requests
import time
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('metabase_api_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MetabaseAPIFetcher:
    """
    A comprehensive Metabase API client for fetching report details.
    """
    
    def __init__(self, config_file: str = "metabase_config.env"):
        """
        Initialize the Metabase API fetcher.
        
        Args:
            config_file (str): Path to the configuration file
        """
        self.config_file = Path(config_file)
        self.base_url = None
        self.api_key = None
        self.session = requests.Session()
        self.api_delay = 0.5  # Default delay between API calls
        self.request_timeout = 30  # Default timeout
        
        # Load configuration
        self._load_config()
        self._setup_session()
        
        # Results storage
        self.successful_fetches = []
        self.failed_fetches = []
        
    def _load_config(self) -> None:
        """Load configuration from environment file."""
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"Configuration file '{self.config_file}' not found. "
                f"Please create it with your Metabase credentials."
            )
        
        # Load environment variables
        load_dotenv(self.config_file)
        
        self.base_url = os.getenv('METABASE_BASE_URL')
        self.api_key = os.getenv('METABASE_API_KEY')
        
        if not self.base_url or not self.api_key:
            raise ValueError(
                "Missing required configuration. Please set METABASE_BASE_URL "
                "and METABASE_API_KEY in your configuration file."
            )
        
        # Remove trailing slash from base URL
        self.base_url = self.base_url.rstrip('/')
        
        # Load optional settings
        try:
            self.api_delay = float(os.getenv('API_DELAY_SECONDS', '0.5'))
            self.request_timeout = int(os.getenv('REQUEST_TIMEOUT_SECONDS', '30'))
        except (ValueError, TypeError):
            logger.warning("Invalid API settings in config, using defaults")
            self.api_delay = 0.5
            self.request_timeout = 30
        
        logger.info(f"✅ Configuration loaded from {self.config_file}")
        logger.info(f"📍 Metabase URL: {self.base_url}")
        logger.info(f"⏱️  API delay: {self.api_delay}s, Timeout: {self.request_timeout}s")
    
    def _setup_session(self) -> None:
        """Setup requests session with authentication headers."""
        self.session.headers.update({
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'MetabaseAPIFetcher/1.0'
        })
        
        # Set timeout for all requests
        self.session.timeout = self.request_timeout
    
    def test_connection(self) -> bool:
        """
        Test the connection to Metabase API.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info("🔍 Testing Metabase API connection...")
            
            # Try to fetch user info as a connection test
            response = self.session.get(f"{self.base_url}/api/user/current")
            response.raise_for_status()
            
            user_info = response.json()
            logger.info(f"✅ Connected successfully! User: {user_info.get('email', 'Unknown')}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Connection test failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during connection test: {str(e)}")
            return False
    
    def fetch_card_details(self, card_id: int) -> Optional[Dict]:
        """
        Fetch detailed information for a specific card/report.
        
        Args:
            card_id (int): The Metabase card/report ID
            
        Returns:
            Optional[Dict]: Card details if successful, None if failed
        """
        try:
            logger.debug(f"📊 Fetching details for card ID: {card_id}")
            
            # Fetch card metadata
            response = self.session.get(f"{self.base_url}/api/card/{card_id}")
            response.raise_for_status()
            
            card_data = response.json()
            
            # Extract key information
            result = {
                'report_id': card_id,
                'report_name': card_data.get('name', 'N/A'),
                'description': card_data.get('description') or 'No description available',
                'sql_query': self._extract_sql_query(card_data),
                'created_at': card_data.get('created_at'),
                'updated_at': card_data.get('updated_at'),
                'collection_id': card_data.get('collection_id'),
                'database_id': card_data.get('database_id'),
                'query_type': card_data.get('query_type', 'unknown')
            }
            
            # Add to successful fetches
            self.successful_fetches.append(result)
            logger.debug(f"✅ Successfully fetched card {card_id}: {result['report_name']}")
            
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                error_msg = f"Card {card_id} not found (possibly deleted/archived)"
                logger.warning(f"⚠️  {error_msg}")
                self.failed_fetches.append({
                    'report_id': card_id,
                    'error': 'Not Found (404)',
                    'details': error_msg
                })
            else:
                error_msg = f"HTTP {e.response.status_code} error for card {card_id}"
                logger.error(f"❌ {error_msg}")
                self.failed_fetches.append({
                    'report_id': card_id,
                    'error': f'HTTP {e.response.status_code}',
                    'details': error_msg
                })
            return None
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error fetching card {card_id}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.failed_fetches.append({
                'report_id': card_id,
                'error': 'Network Error',
                'details': error_msg
            })
            return None
            
        except Exception as e:
            error_msg = f"Unexpected error fetching card {card_id}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.failed_fetches.append({
                'report_id': card_id,
                'error': 'Unexpected Error',
                'details': error_msg
            })
            return None
    
    def _extract_sql_query(self, card_data: Dict) -> str:
        """
        Extract the complete SQL query from card data.
        
        Args:
            card_data (Dict): The card data from Metabase API
            
        Returns:
            str: The extracted SQL query or appropriate message
        """
        try:
            dataset_query = card_data.get('dataset_query', {})
            
            # Handle native SQL queries
            if dataset_query.get('type') == 'native':
                native_query = dataset_query.get('native', {})
                sql_query = native_query.get('query', '')
                
                if sql_query:
                    return sql_query.strip()
                else:
                    return "No SQL query found in native query"
            
            # Handle GUI-built queries (convert to readable format)
            elif dataset_query.get('type') == 'query':
                query_info = dataset_query.get('query', {})
                return f"GUI Query: {json.dumps(query_info, indent=2)}"
            
            else:
                return f"Unknown query type: {dataset_query.get('type', 'N/A')}"
                
        except Exception as e:
            logger.warning(f"Error extracting SQL query: {str(e)}")
            return "Error extracting SQL query"
    
    def load_report_ids_from_excel(self, excel_file: str) -> List[int]:
        """
        Load report IDs from Excel file.
        
        Args:
            excel_file (str): Path to the Excel file
            
        Returns:
            List[int]: List of report IDs
        """
        try:
            logger.info(f"📖 Loading report IDs from {excel_file}")
            
            # Read Excel file
            df = pd.read_excel(excel_file, engine='openpyxl')
            
            # Check if 'Report ID' column exists
            if 'Report ID' not in df.columns:
                available_cols = ', '.join(df.columns.tolist())
                raise ValueError(
                    f"'Report ID' column not found. Available columns: {available_cols}"
                )
            
            # Extract report IDs and convert to integers
            report_ids = df['Report ID'].dropna().astype(int).tolist()
            
            logger.info(f"✅ Loaded {len(report_ids)} report IDs from Excel")
            logger.info(f"📊 Report ID range: {min(report_ids)} to {max(report_ids)}")
            
            return report_ids
            
        except Exception as e:
            logger.error(f"❌ Error loading Excel file: {str(e)}")
            raise
    
    def fetch_all_reports(self, report_ids: List[int], max_reports: Optional[int] = None) -> pd.DataFrame:
        """
        Fetch details for all report IDs with progress tracking.
        
        Args:
            report_ids (List[int]): List of report IDs to fetch
            max_reports (Optional[int]): Maximum number of reports to fetch (for testing)
            
        Returns:
            pd.DataFrame: DataFrame containing all successfully fetched reports
        """
        # Limit number of reports if specified (useful for testing)
        if max_reports:
            report_ids = report_ids[:max_reports]
            logger.info(f"🔬 Testing mode: Processing only first {max_reports} reports")
        
        total_reports = len(report_ids)
        logger.info(f"🚀 Starting to fetch {total_reports} reports...")
        logger.info(f"⏱️  Estimated time: {total_reports * self.api_delay / 60:.1f} minutes")
        
        start_time = datetime.now()
        
        for i, report_id in enumerate(report_ids, 1):
            # Progress logging
            if i % 50 == 0 or i == total_reports:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = i / elapsed if elapsed > 0 else 0
                eta = (total_reports - i) / rate if rate > 0 else 0
                
                logger.info(
                    f"📈 Progress: {i}/{total_reports} ({i/total_reports*100:.1f}%) | "
                    f"Rate: {rate:.1f}/min | ETA: {eta/60:.1f}min"
                )
            
            # Fetch report details
            self.fetch_card_details(report_id)
            
            # Respectful delay between requests (except for the last one)
            if i < total_reports:
                time.sleep(self.api_delay)
        
        # Create DataFrame from successful fetches
        if self.successful_fetches:
            df = pd.DataFrame(self.successful_fetches)
            logger.info(f"✅ Successfully fetched {len(df)} reports")
        else:
            df = pd.DataFrame()
            logger.warning("⚠️  No reports were successfully fetched")
        
        # Log summary
        total_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"⏱️  Total processing time: {total_time/60:.1f} minutes")
        logger.info(f"✅ Successful: {len(self.successful_fetches)}")
        logger.info(f"❌ Failed: {len(self.failed_fetches)}")
        
        return df
    
    def save_results(self, df: pd.DataFrame, output_file: str = None) -> str:
        """
        Save results to Excel file with error summary.
        
        Args:
            df (pd.DataFrame): DataFrame with successful results
            output_file (str, optional): Output file path
            
        Returns:
            str: Path to the saved file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"metabase_reports_detailed_{timestamp}.xlsx"
        
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Main results
                if not df.empty:
                    df.to_excel(writer, sheet_name='Report Details', index=False)
                    logger.info(f"💾 Saved {len(df)} successful results to 'Report Details' sheet")
                
                # Error summary
                if self.failed_fetches:
                    error_df = pd.DataFrame(self.failed_fetches)
                    error_df.to_excel(writer, sheet_name='Failed Fetches', index=False)
                    logger.info(f"⚠️  Saved {len(error_df)} failed fetches to 'Failed Fetches' sheet")
                
                # Summary statistics
                summary_data = {
                    'Metric': [
                        'Total Reports Processed',
                        'Successful Fetches',
                        'Failed Fetches',
                        'Success Rate (%)',
                        'Processing Date'
                    ],
                    'Value': [
                        len(self.successful_fetches) + len(self.failed_fetches),
                        len(self.successful_fetches),
                        len(self.failed_fetches),
                        (len(self.successful_fetches) / 
                         (len(self.successful_fetches) + len(self.failed_fetches)) * 100 
                         if (len(self.successful_fetches) + len(self.failed_fetches)) > 0 else 0),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            logger.info(f"📄 Results saved to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {str(e)}")
            raise
    
    def print_sample_results(self, df: pd.DataFrame, num_samples: int = 3) -> None:
        """
        Print sample results for verification.
        
        Args:
            df (pd.DataFrame): Results DataFrame
            num_samples (int): Number of samples to display
        """
        if df.empty:
            logger.warning("⚠️  No results to display")
            return
        
        print(f"\n📋 SAMPLE RESULTS ({min(num_samples, len(df))} of {len(df)} reports):")
        print("=" * 80)
        
        for i, (_, row) in enumerate(df.head(num_samples).iterrows()):
            print(f"\n🔸 Report #{i+1}:")
            print(f"   ID: {row['report_id']}")
            print(f"   Name: {row['report_name'][:60]}...")
            print(f"   Description: {row['description'][:60]}...")
            print(f"   SQL Preview: {row['sql_query'][:80]}...")
            print(f"   Updated: {row['updated_at']}")


def main():
    """Main execution function."""
    print("🚀 Metabase API Report Fetcher")
    print("=" * 50)
    
    try:
        # Initialize fetcher
        fetcher = MetabaseAPIFetcher()
        
        # Test connection
        if not fetcher.test_connection():
            print("❌ Cannot proceed without valid Metabase connection.")
            return
        
        # Load report IDs from Excel
        excel_file = "metabase_reports_analysis.xlsx"
        report_ids = fetcher.load_report_ids_from_excel(excel_file)
        
        # Ask user about testing mode
        print(f"\n📊 Found {len(report_ids)} reports to process.")
        
        # For initial testing, process a smaller subset
        test_mode = input("🔬 Run in test mode with first 10 reports? (y/N): ").lower().strip()
        max_reports = 10 if test_mode == 'y' else None
        
        if test_mode == 'y':
            print("🧪 Running in test mode...")
        else:
            confirm = input(f"⚠️  This will process ALL {len(report_ids)} reports. Continue? (y/N): ").lower().strip()
            if confirm != 'y':
                print("🛑 Operation cancelled by user.")
                return
        
        # Fetch all reports
        results_df = fetcher.fetch_all_reports(report_ids, max_reports)
        
        # Display sample results
        fetcher.print_sample_results(results_df)
        
        # Save results
        output_file = fetcher.save_results(results_df)
        
        print(f"\n✅ Process completed successfully!")
        print(f"📄 Results saved to: {output_file}")
        print(f"📊 Final Summary:")
        print(f"   ✅ Successful: {len(fetcher.successful_fetches)}")
        print(f"   ❌ Failed: {len(fetcher.failed_fetches)}")
        
        if fetcher.failed_fetches:
            print(f"\n⚠️  Some reports failed to fetch. Check the 'Failed Fetches' sheet in {output_file}")
        
        # Return DataFrame for further processing
        return results_df
        
    except KeyboardInterrupt:
        logger.info("🛑 Process interrupted by user")
        print("\n🛑 Process interrupted by user")
        
    except Exception as e:
        logger.error(f"💥 Fatal error: {str(e)}")
        print(f"\n💥 Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    main() 