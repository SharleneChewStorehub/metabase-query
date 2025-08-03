#!/usr/bin/env python3
"""
Metabase Active Reports Fetcher v2

A script to fetch Metabase reports that have been actively used or updated
within the last 12 months, using available API endpoints and smart heuristics.

Since /api/activity endpoint is not available, this version uses:
- Recent update timestamps to indicate usage
- Cross-referencing with existing report data
- Smart filtering based on multiple indicators

Features:
- Works with limited API endpoints
- Uses update timestamps as usage indicators
- Maintains same column structure as original Excel file
- READ-ONLY operations only (GET requests only)
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
        logging.FileHandler('metabase_active_reports_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MetabaseActiveReportsFetcherV2:
    """
    Enhanced Metabase API client that works with limited endpoints to identify active reports.
    
    SAFETY PROTOCOL: This class performs ONLY READ-ONLY operations using GET requests.
    """
    
    def __init__(self, config_file: str = "metabase_config.env"):
        """Initialize the fetcher."""
        self.config_file = Path(config_file)
        self.base_url = None
        self.api_key = None
        self.session = requests.Session()
        self.api_delay = 0.5
        self.request_timeout = 30
        
        # Results storage
        self.successful_fetches = []
        self.failed_fetches = []
        
        # Date ranges for activity analysis
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=365)
        self.recent_activity_cutoff = self.end_date - timedelta(days=90)  # 3 months for "recent"
        
        # Load configuration
        self._load_config()
        self._setup_session()
        
        logger.info("🔒 SAFETY PROTOCOL: This script performs READ-ONLY operations only")
        logger.info("✅ Only GET requests will be made to the Metabase API")
        
    def _load_config(self) -> None:
        """Load configuration from environment file."""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file '{self.config_file}' not found.")
        
        load_dotenv(self.config_file)
        
        self.base_url = os.getenv('METABASE_BASE_URL')
        self.api_key = os.getenv('METABASE_API_KEY')
        
        if not self.base_url or not self.api_key:
            raise ValueError("Missing required configuration in config file.")
        
        self.base_url = self.base_url.rstrip('/')
        
        try:
            self.api_delay = float(os.getenv('API_DELAY_SECONDS', '0.5'))
            self.request_timeout = int(os.getenv('REQUEST_TIMEOUT_SECONDS', '30'))
        except (ValueError, TypeError):
            self.api_delay = 0.5
            self.request_timeout = 30
        
        logger.info(f"✅ Configuration loaded from {self.config_file}")
        logger.info(f"📍 Metabase URL: {self.base_url}")
        logger.info(f"📅 Activity date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
    
    def _setup_session(self) -> None:
        """Setup requests session with authentication headers."""
        self.session.headers.update({
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'MetabaseActiveReportsFetcherV2/1.0 (READ-ONLY)'
        })
        self.session.timeout = self.request_timeout
    
    def test_connection(self) -> bool:
        """Test the connection to Metabase API."""
        try:
            logger.info("🔍 Testing Metabase API connection...")
            response = self.session.get(f"{self.base_url}/api/user/current")
            response.raise_for_status()
            
            user_info = response.json()
            logger.info(f"✅ Connected successfully! User: {user_info.get('email', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection test failed: {str(e)}")
            return False
    
    def fetch_all_cards(self) -> List[Dict]:
        """Fetch all cards from Metabase API."""
        try:
            logger.info("📋 Fetching all cards...")
            response = self.session.get(f"{self.base_url}/api/card")
            response.raise_for_status()
            
            cards = response.json()
            logger.info(f"✅ Fetched {len(cards)} total cards")
            return cards
            
        except Exception as e:
            logger.error(f"❌ Error fetching cards: {str(e)}")
            return []
    
    def analyze_card_activity(self, cards: List[Dict]) -> List[Dict]:
        """
        Analyze cards to determine which ones show signs of recent activity.
        
        Activity indicators:
        1. Recently updated (within last 12 months)
        2. Recently created (within last 12 months) 
        3. Non-archived status
        4. Has meaningful content (not just empty queries)
        """
        logger.info("🔍 Analyzing cards for activity indicators...")
        
        active_cards = []
        activity_counts = defaultdict(int)
        
        for card in cards:
            try:
                # Parse timestamps
                created_at = self._parse_timestamp(card.get('created_at'))
                updated_at = self._parse_timestamp(card.get('updated_at'))
                
                if not updated_at:
                    continue
                
                # Calculate activity score based on multiple factors
                activity_score = 0
                activity_reasons = []
                
                # Recent updates (within 12 months)
                if updated_at >= self.start_date:
                    activity_score += 2
                    activity_reasons.append("Updated in last 12 months")
                
                # Very recent updates (within 3 months) 
                if updated_at >= self.recent_activity_cutoff:
                    activity_score += 3
                    activity_reasons.append("Recently updated (3 months)")
                
                # Recent creation
                if created_at and created_at >= self.start_date:
                    activity_score += 1
                    activity_reasons.append("Created in last 12 months")
                
                # Not archived
                if not card.get('archived', False):
                    activity_score += 1
                    activity_reasons.append("Not archived")
                
                # Has description (indicates curation)
                if card.get('description'):
                    activity_score += 1
                    activity_reasons.append("Has description")
                
                # Has collection (organized)
                if card.get('collection_id'):
                    activity_score += 1
                    activity_reasons.append("In collection")
                
                # Estimate usage frequency based on update frequency
                if created_at and updated_at > created_at:
                    days_since_creation = (self.end_date - created_at).days
                    days_since_update = (self.end_date - updated_at).days
                    
                    if days_since_creation > 0:
                        # Rough estimate: more recent updates = more usage
                        estimated_usage = max(1, int(10 * (365 - days_since_update) / 365))
                        if days_since_update < 30:  # Very recent
                            estimated_usage *= 2
                    else:
                        estimated_usage = 1
                else:
                    estimated_usage = 1
                
                # Include cards with activity score >= 2
                if activity_score >= 2:
                    card_info = {
                        'report_id': card['id'],
                        'report_name': card.get('name', 'N/A'),
                        'description': card.get('description') or 'No description available', 
                        'created_at': card.get('created_at'),
                        'updated_at': card.get('updated_at'),
                        'collection_id': card.get('collection_id'),
                        'database_id': card.get('database_id'),
                        'query_type': card.get('query_type', 'unknown'),
                        'activity_score': activity_score,
                        'activity_reasons': ', '.join(activity_reasons),
                        'estimated_usage_last_12_months': estimated_usage,
                        'archived': card.get('archived', False)
                    }
                    active_cards.append(card_info)
                    
            except Exception as e:
                logger.debug(f"Error analyzing card {card.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"✅ Found {len(active_cards)} cards with activity indicators")
        return active_cards
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object."""
        if not timestamp_str:
            return None
        
        try:
            # Handle ISO format with Z
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            try:
                # Try alternative format
                return datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            except:
                return None
    
    def fetch_detailed_card_info(self, card_id: int) -> Optional[Dict]:
        """Fetch detailed information for a specific card."""
        try:
            logger.debug(f"📊 Fetching details for card ID: {card_id}")
            
            response = self.session.get(f"{self.base_url}/api/card/{card_id}")
            response.raise_for_status()
            
            card_data = response.json()
            
            # Extract SQL query
            sql_query = self._extract_sql_query(card_data)
            
            return {
                'sql_query': sql_query
            }
            
        except Exception as e:
            logger.debug(f"Error fetching details for card {card_id}: {e}")
            return None
    
    def _extract_sql_query(self, card_data: Dict) -> str:
        """Extract SQL query from card data."""
        try:
            dataset_query = card_data.get('dataset_query', {})
            
            if dataset_query.get('type') == 'native':
                native_query = dataset_query.get('native', {})
                sql_query = native_query.get('query', '')
                return sql_query.strip() if sql_query else "No SQL query found"
            
            elif dataset_query.get('type') == 'query':
                query_info = dataset_query.get('query', {})
                return f"GUI Query: {json.dumps(query_info, indent=2)}"
            
            else:
                return f"Unknown query type: {dataset_query.get('type', 'N/A')}"
                
        except Exception as e:
            return "Error extracting SQL query"
    
    def fetch_active_reports_with_estimates(self, min_activity_score: int = 2) -> pd.DataFrame:
        """
        Fetch reports that show signs of activity with estimated usage statistics.
        
        Args:
            min_activity_score: Minimum activity score to include a report
        """
        logger.info(f"🚀 Starting to fetch active reports with minimum activity score: {min_activity_score}")
        start_time = datetime.now()
        
        # Step 1: Fetch all cards
        all_cards = self.fetch_all_cards()
        if not all_cards:
            logger.error("No cards retrieved")
            return pd.DataFrame()
        
        time.sleep(self.api_delay)
        
        # Step 2: Analyze activity
        active_cards = self.analyze_card_activity(all_cards)
        
        # Step 3: Filter by activity score
        filtered_cards = [card for card in active_cards if card['activity_score'] >= min_activity_score]
        
        logger.info(f"📊 Found {len(filtered_cards)} cards with activity score >= {min_activity_score}")
        
        if not filtered_cards:
            logger.warning("⚠️  No cards found with sufficient activity")
            return pd.DataFrame()
        
        # Step 4: Fetch detailed information for active cards
        logger.info(f"📋 Fetching detailed information for {len(filtered_cards)} active cards...")
        
        for i, card_info in enumerate(filtered_cards, 1):
            # Progress logging
            if i % 50 == 0 or i == len(filtered_cards):
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(filtered_cards) - i) / rate if rate > 0 else 0
                
                logger.info(
                    f"📈 Progress: {i}/{len(filtered_cards)} ({i/len(filtered_cards)*100:.1f}%) | "
                    f"Rate: {rate:.1f}/min | ETA: {eta/60:.1f}min"
                )
            
            # Fetch detailed card info
            detailed_info = self.fetch_detailed_card_info(card_info['report_id'])
            
            if detailed_info:
                card_info.update(detailed_info)
                self.successful_fetches.append(card_info)
            else:
                self.failed_fetches.append({
                    'report_id': card_info['report_id'],
                    'error': 'Failed to fetch details',
                    'activity_score': card_info['activity_score']
                })
            
            # Respectful delay
            if i < len(filtered_cards):
                time.sleep(self.api_delay)
        
        # Create DataFrame
        if self.successful_fetches:
            df = pd.DataFrame(self.successful_fetches)
            # Sort by estimated usage descending
            df = df.sort_values('estimated_usage_last_12_months', ascending=False)
            logger.info(f"✅ Successfully fetched {len(df)} active reports")
        else:
            df = pd.DataFrame()
            logger.warning("⚠️  No reports were successfully fetched")
        
        total_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"⏱️  Total processing time: {total_time/60:.1f} minutes")
        logger.info(f"✅ Successful: {len(self.successful_fetches)}")
        logger.info(f"❌ Failed: {len(self.failed_fetches)}")
        
        return df
    
    def save_results(self, df: pd.DataFrame, output_file: str = None) -> str:
        """Save results to Excel file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"metabase_active_reports_estimated_usage_{timestamp}.xlsx"
        
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Main results
                if not df.empty:
                    # Rename column for clarity
                    df_output = df.copy()
                    df_output = df_output.rename(columns={
                        'estimated_usage_last_12_months': 'estimated_usage_count_last_12_months'
                    })
                    
                    df_output.to_excel(writer, sheet_name='Active Reports (Estimated)', index=False)
                    logger.info(f"💾 Saved {len(df_output)} active reports")
                
                # Error summary
                if self.failed_fetches:
                    error_df = pd.DataFrame(self.failed_fetches)
                    error_df.to_excel(writer, sheet_name='Failed Fetches', index=False)
                    logger.info(f"⚠️  Saved {len(error_df)} failed fetches")
                
                # Summary statistics
                total_estimated_usage = df['estimated_usage_last_12_months'].sum() if not df.empty else 0
                avg_estimated_usage = df['estimated_usage_last_12_months'].mean() if not df.empty else 0
                
                summary_data = {
                    'Metric': [
                        'Analysis Method',
                        'Date Range',
                        'Total Active Reports',
                        'Failed Fetches',
                        'Total Estimated Usage',
                        'Average Estimated Usage',
                        'Most Active Report',
                        'Processing Date'
                    ],
                    'Value': [
                        'Activity Score & Update Patterns',
                        f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}",
                        len(self.successful_fetches),
                        len(self.failed_fetches),
                        int(total_estimated_usage),
                        f"{avg_estimated_usage:.1f}",
                        df.iloc[0]['report_name'] if not df.empty else 'N/A',
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
        """Print sample results for verification."""
        if df.empty:
            logger.warning("⚠️  No results to display")
            return
        
        print(f"\n📋 SAMPLE ACTIVE REPORTS ({min(num_samples, len(df))} of {len(df)} reports):")
        print("=" * 100)
        
        for i, (_, row) in enumerate(df.head(num_samples).iterrows()):
            print(f"\n🔸 Report #{i+1}:")
            print(f"   ID: {row['report_id']}")
            print(f"   Name: {row['report_name'][:80]}...")
            print(f"   Est. Usage (12 months): {row['estimated_usage_last_12_months']} times")
            print(f"   Activity Score: {row['activity_score']}")
            print(f"   Activity Reasons: {row['activity_reasons']}")
            print(f"   Last Updated: {row['updated_at']}")
            print(f"   Query Type: {row['query_type']}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Fetch active Metabase reports with estimated usage')
    parser.add_argument('--min-activity-score', type=int, default=2,
                       help='Minimum activity score to include a report (default: 2)')
    parser.add_argument('--config', type=str, default='metabase_config.env',
                       help='Configuration file path')
    parser.add_argument('--output', type=str,
                       help='Output Excel file path')
    
    args = parser.parse_args()
    
    print("🚀 Metabase Active Reports Fetcher v2")
    print("=" * 60)
    print("🔒 SAFETY PROTOCOL: READ-ONLY operations only")
    print("✅ Only GET requests will be made")
    print("🧠 Uses smart heuristics for activity estimation")
    print("=" * 60)
    
    try:
        # Initialize fetcher
        fetcher = MetabaseActiveReportsFetcherV2(config_file=args.config)
        
        # Test connection
        if not fetcher.test_connection():
            print("❌ Cannot proceed without valid Metabase connection.")
            return
        
        print(f"\n📊 Fetching reports with minimum activity score: {args.min_activity_score}")
        print(f"📅 Date range: {fetcher.start_date.strftime('%Y-%m-%d')} to {fetcher.end_date.strftime('%Y-%m-%d')}")
        print(f"🧠 Activity indicators: recent updates, not archived, has description, in collection")
        
        # Confirm with user
        confirm = input(f"\n⚠️  This will analyze all {fetcher.end_date.year} activity patterns. Continue? (y/N): ").lower().strip()
        if confirm != 'y':
            print("🛑 Operation cancelled by user.")
            return
        
        # Fetch active reports
        results_df = fetcher.fetch_active_reports_with_estimates(min_activity_score=args.min_activity_score)
        
        if results_df.empty:
            print(f"\n⚠️  No active reports found with activity score >= {args.min_activity_score}")
            print("💡 Try lowering --min-activity-score (minimum: 1)")
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
        print(f"   📈 Total Estimated Usage: {results_df['estimated_usage_last_12_months'].sum()}")
        print(f"   📊 Average Estimated Usage: {results_df['estimated_usage_last_12_months'].mean():.1f}")
        
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