#!/usr/bin/env python3
"""
Metabase Active Reports Fetcher

A script to fetch Metabase reports that have been actively used (queried, viewed, or accessed)
within the last 12 months, including usage statistics.

Features:
- Fetches only reports that have been used in the last 12 months
- Includes usage count for each report
- Maintains same column structure as original Excel file
- Adds usage statistics column
- READ-ONLY operations only (GET requests only)
- Robust error handling and progress tracking

CRITICAL SAFETY PROTOCOL:
This script ONLY performs READ-ONLY operations using GET requests.
NO data modification, creation, archiving, or deletion operations are performed.
"""

import pandas as pd
import requests
import time
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
from collections import defaultdict
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('metabase_active_reports_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MetabaseActiveReportsFetcher:
    """
    A comprehensive Metabase API client for fetching active reports with usage statistics.
    
    SAFETY PROTOCOL: This class performs ONLY READ-ONLY operations using GET requests.
    """
    
    def __init__(self, config_file: str = "metabase_config.env"):
        """
        Initialize the Metabase Active Reports fetcher.
        
        Args:
            config_file (str): Path to the configuration file
        """
        self.config_file = Path(config_file)
        self.base_url = None
        self.api_key = None
        self.session = requests.Session()
        self.api_delay = 0.5  # Default delay between API calls
        self.request_timeout = 30  # Default timeout
        
        # Results storage
        self.successful_fetches = []
        self.failed_fetches = []
        self.activity_data = []
        self.usage_stats = defaultdict(int)
        
        # Date range for activity filtering (last 12 months)
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=365)
        
        # Load configuration
        self._load_config()
        self._setup_session()
        
        logger.info("🔒 SAFETY PROTOCOL: This script performs READ-ONLY operations only")
        logger.info("✅ Only GET requests will be made to the Metabase API")
        
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
        logger.info(f"📅 Activity date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
    
    def _setup_session(self) -> None:
        """Setup requests session with authentication headers."""
        self.session.headers.update({
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'MetabaseActiveReportsFetcher/1.0 (READ-ONLY)'
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
            
            # Try to fetch user info as a connection test (READ-ONLY operation)
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
    
    def fetch_activity_data(self) -> Dict:
        """
        Fetch activity data from Metabase API (READ-ONLY operation).
        
        Returns:
            Dict: Activity data from the API
        """
        try:
            logger.info("📊 Fetching activity data...")
            
            # Fetch general activity data (READ-ONLY operation)
            response = self.session.get(f"{self.base_url}/api/activity")
            response.raise_for_status()
            
            activity_data = response.json()
            logger.info(f"✅ Fetched {len(activity_data)} activity records")
            
            return activity_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error fetching activity data: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching activity data: {str(e)}")
            return []
    
    def fetch_recent_views(self) -> List[Dict]:
        """
        Fetch recent views data from Metabase API (READ-ONLY operation).
        
        Returns:
            List[Dict]: Recent views data
        """
        try:
            logger.info("👀 Fetching recent views data...")
            
            # Fetch recent views (READ-ONLY operation)
            response = self.session.get(f"{self.base_url}/api/activity/recent_views")
            response.raise_for_status()
            
            recent_views = response.json()
            logger.info(f"✅ Fetched {len(recent_views)} recent view records")
            
            return recent_views
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error fetching recent views: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching recent views: {str(e)}")
            return []
    
    def fetch_all_cards(self) -> List[Dict]:
        """
        Fetch all cards/reports from Metabase API (READ-ONLY operation).
        
        Returns:
            List[Dict]: List of all cards
        """
        try:
            logger.info("📋 Fetching all cards...")
            
            # Fetch all cards (READ-ONLY operation)
            response = self.session.get(f"{self.base_url}/api/card")
            response.raise_for_status()
            
            cards = response.json()
            logger.info(f"✅ Fetched {len(cards)} total cards")
            
            return cards
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error fetching cards: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching cards: {str(e)}")
            return []
    
    def analyze_activity_for_usage(self, activity_data: List[Dict], recent_views: List[Dict]) -> Dict[int, int]:
        """
        Analyze activity data to count usage for each card within the last 12 months.
        
        Args:
            activity_data: Activity data from API
            recent_views: Recent views data from API
            
        Returns:
            Dict[int, int]: Mapping of card_id to usage count
        """
        logger.info("🔍 Analyzing activity data for usage statistics...")
        
        usage_counts = defaultdict(int)
        
        # Process general activity data
        for activity in activity_data:
            try:
                # Parse timestamp
                if 'timestamp' in activity:
                    timestamp_str = activity['timestamp']
                    # Handle different timestamp formats
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        continue
                    
                    # Check if within last 12 months
                    if timestamp >= self.start_date:
                        # Look for card-related activities
                        if activity.get('topic') == 'card' or 'card' in str(activity.get('details', {})):
                            model_id = activity.get('model_id')
                            if model_id and isinstance(model_id, int):
                                usage_counts[model_id] += 1
                
            except Exception as e:
                logger.debug(f"Error processing activity record: {e}")
                continue
        
        # Process recent views data
        for view in recent_views:
            try:
                if view.get('model') == 'card':
                    model_id = view.get('model_id')
                    if model_id and isinstance(model_id, int):
                        usage_counts[model_id] += 1
                        
            except Exception as e:
                logger.debug(f"Error processing recent view record: {e}")
                continue
        
        logger.info(f"✅ Analyzed usage for {len(usage_counts)} cards")
        return dict(usage_counts)
    
    def fetch_card_details(self, card_id: int) -> Optional[Dict]:
        """
        Fetch detailed information for a specific card/report (READ-ONLY operation).
        
        Args:
            card_id (int): The Metabase card/report ID
            
        Returns:
            Optional[Dict]: Card details if successful, None if failed
        """
        try:
            logger.debug(f"📊 Fetching details for card ID: {card_id}")
            
            # Fetch card metadata (READ-ONLY operation)
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
            
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.debug(f"Card {card_id} not found (possibly deleted/archived)")
            else:
                logger.debug(f"HTTP {e.response.status_code} error for card {card_id}")
            return None
            
        except Exception as e:
            logger.debug(f"Error fetching card {card_id}: {str(e)}")
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
    
    def fetch_active_reports_with_usage(self, min_usage_count: int = 1) -> pd.DataFrame:
        """
        Fetch reports that have been actively used in the last 12 months with usage statistics.
        
        Args:
            min_usage_count (int): Minimum usage count to include a report
            
        Returns:
            pd.DataFrame: DataFrame containing active reports with usage statistics
        """
        logger.info(f"🚀 Starting to fetch active reports with minimum usage: {min_usage_count}")
        start_time = datetime.now()
        
        # Step 1: Fetch activity data
        activity_data = self.fetch_activity_data()
        time.sleep(self.api_delay)
        
        # Step 2: Fetch recent views
        recent_views = self.fetch_recent_views()
        time.sleep(self.api_delay)
        
        # Step 3: Analyze usage
        usage_stats = self.analyze_activity_for_usage(activity_data, recent_views)
        
        # Step 4: Filter cards with sufficient usage
        active_card_ids = [card_id for card_id, count in usage_stats.items() if count >= min_usage_count]
        
        logger.info(f"📊 Found {len(active_card_ids)} cards with usage >= {min_usage_count} in last 12 months")
        
        if not active_card_ids:
            logger.warning("⚠️  No cards found with sufficient usage")
            return pd.DataFrame()
        
        # Step 5: Fetch detailed information for active cards
        logger.info(f"📋 Fetching detailed information for {len(active_card_ids)} active cards...")
        
        for i, card_id in enumerate(active_card_ids, 1):
            # Progress logging
            if i % 50 == 0 or i == len(active_card_ids):
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(active_card_ids) - i) / rate if rate > 0 else 0
                
                logger.info(
                    f"📈 Progress: {i}/{len(active_card_ids)} ({i/len(active_card_ids)*100:.1f}%) | "
                    f"Rate: {rate:.1f}/min | ETA: {eta/60:.1f}min"
                )
            
            # Fetch card details
            card_details = self.fetch_card_details(card_id)
            
            if card_details:
                # Add usage statistics
                card_details['usage_count_last_12_months'] = usage_stats[card_id]
                self.successful_fetches.append(card_details)
            else:
                self.failed_fetches.append({
                    'report_id': card_id,
                    'error': 'Failed to fetch details',
                    'usage_count': usage_stats[card_id]
                })
            
            # Respectful delay between requests
            if i < len(active_card_ids):
                time.sleep(self.api_delay)
        
        # Create DataFrame from successful fetches
        if self.successful_fetches:
            df = pd.DataFrame(self.successful_fetches)
            # Sort by usage count descending
            df = df.sort_values('usage_count_last_12_months', ascending=False)
            logger.info(f"✅ Successfully fetched {len(df)} active reports")
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
            output_file = f"metabase_active_reports_last_12_months_{timestamp}.xlsx"
        
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Main results
                if not df.empty:
                    df.to_excel(writer, sheet_name='Active Reports (12 Months)', index=False)
                    logger.info(f"💾 Saved {len(df)} active reports to 'Active Reports (12 Months)' sheet")
                
                # Error summary
                if self.failed_fetches:
                    error_df = pd.DataFrame(self.failed_fetches)
                    error_df.to_excel(writer, sheet_name='Failed Fetches', index=False)
                    logger.info(f"⚠️  Saved {len(error_df)} failed fetches to 'Failed Fetches' sheet")
                
                # Summary statistics
                total_usage = df['usage_count_last_12_months'].sum() if not df.empty else 0
                avg_usage = df['usage_count_last_12_months'].mean() if not df.empty else 0
                
                summary_data = {
                    'Metric': [
                        'Date Range',
                        'Total Active Reports',
                        'Failed Fetches',
                        'Total Usage Count',
                        'Average Usage Per Report',
                        'Most Used Report',
                        'Least Used Report',
                        'Processing Date'
                    ],
                    'Value': [
                        f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}",
                        len(self.successful_fetches),
                        len(self.failed_fetches),
                        int(total_usage),
                        f"{avg_usage:.1f}",
                        df.iloc[0]['report_name'] if not df.empty else 'N/A',
                        df.iloc[-1]['report_name'] if not df.empty else 'N/A',
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
    
    def print_sample_results(self, df: pd.DataFrame, num_samples: int = 5) -> None:
        """
        Print sample results for verification.
        
        Args:
            df (pd.DataFrame): Results DataFrame
            num_samples (int): Number of samples to display
        """
        if df.empty:
            logger.warning("⚠️  No results to display")
            return
        
        print(f"\n📋 SAMPLE ACTIVE REPORTS ({min(num_samples, len(df))} of {len(df)} reports):")
        print("=" * 100)
        
        for i, (_, row) in enumerate(df.head(num_samples).iterrows()):
            print(f"\n🔸 Report #{i+1}:")
            print(f"   ID: {row['report_id']}")
            print(f"   Name: {row['report_name'][:80]}...")
            print(f"   Usage (12 months): {row['usage_count_last_12_months']} times")
            print(f"   Last Updated: {row['updated_at']}")
            print(f"   Query Type: {row['query_type']}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Fetch active Metabase reports with usage statistics')
    parser.add_argument('--min-usage', type=int, default=1, 
                       help='Minimum usage count to include a report (default: 1)')
    parser.add_argument('--config', type=str, default='metabase_config.env',
                       help='Configuration file path (default: metabase_config.env)')
    parser.add_argument('--output', type=str, 
                       help='Output Excel file path (auto-generated if not specified)')
    
    args = parser.parse_args()
    
    print("🚀 Metabase Active Reports Fetcher")
    print("=" * 60)
    print("🔒 SAFETY PROTOCOL: READ-ONLY operations only")
    print("✅ Only GET requests will be made")
    print("=" * 60)
    
    try:
        # Initialize fetcher
        fetcher = MetabaseActiveReportsFetcher(config_file=args.config)
        
        # Test connection
        if not fetcher.test_connection():
            print("❌ Cannot proceed without valid Metabase connection.")
            return
        
        print(f"\n📊 Fetching reports with minimum usage: {args.min_usage}")
        print(f"📅 Date range: {fetcher.start_date.strftime('%Y-%m-%d')} to {fetcher.end_date.strftime('%Y-%m-%d')}")
        
        # Confirm with user
        confirm = input(f"\n⚠️  This will analyze activity for the last 12 months. Continue? (y/N): ").lower().strip()
        if confirm != 'y':
            print("🛑 Operation cancelled by user.")
            return
        
        # Fetch active reports
        results_df = fetcher.fetch_active_reports_with_usage(min_usage_count=args.min_usage)
        
        if results_df.empty:
            print("\n⚠️  No active reports found matching the criteria.")
            return
        
        # Display sample results
        fetcher.print_sample_results(results_df)
        
        # Save results
        output_file = fetcher.save_results(results_df, args.output)
        
        print(f"\n✅ Process completed successfully!")
        print(f"📄 Results saved to: {output_file}")
        print(f"📊 Final Summary:")
        print(f"   ✅ Active Reports: {len(fetcher.successful_fetches)}")
        print(f"   ❌ Failed Fetches: {len(fetcher.failed_fetches)}")
        print(f"   📈 Total Usage Count: {results_df['usage_count_last_12_months'].sum()}")
        print(f"   📊 Average Usage: {results_df['usage_count_last_12_months'].mean():.1f}")
        
        if fetcher.failed_fetches:
            print(f"\n⚠️  Some reports failed to fetch. Check the 'Failed Fetches' sheet in {output_file}")
        
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