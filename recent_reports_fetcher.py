#!/usr/bin/env python3
"""
Recent Reports Fetcher - Metabase Analysis Tool

🚨 CRITICAL SAFETY PROTOCOL: READ-ONLY OPERATIONS ONLY
This script strictly adheres to the Metabase API Safety Protocol:
- ONLY uses GET requests for data retrieval
- NO modifications, deletions, or updates to Metabase instance
- Designed for analysis and reporting purposes only

Purpose:
- Identifies reports viewed in the last 12 months
- Excludes previously analyzed reports
- Fetches full report details with collection names
- Counts view frequency for each report
"""

import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from collections import defaultdict
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('recent_reports_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MetabaseRecentReportsFetcher:
    """
    Fetches recently viewed Metabase reports that haven't been previously processed.
    
    🚨 SAFETY PROTOCOL: All operations are strictly READ-ONLY using GET requests only.
    """
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the fetcher with Metabase connection details.
        
        Args:
            base_url: Metabase instance URL (e.g., 'https://your-metabase.com')
            api_key: Metabase API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        })
        
        # Calculate 12 months ago timestamp
        self.twelve_months_ago = datetime.now() - timedelta(days=365)
        logger.info(f"Looking for reports viewed since: {self.twelve_months_ago.strftime('%Y-%m-%d')}")
        
        # Rate limiting - polite delay between API calls
        self.api_delay = float(os.getenv('API_DELAY_SECONDS', '0.5'))
        
    def _make_api_request(self, endpoint: str, params: dict = None) -> dict:
        """
        Make a safe GET request to the Metabase API.
        
        🚨 SAFETY: Only GET requests are allowed.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters for the request
            
        Returns:
            JSON response data
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Enforce polite delay between API calls
            time.sleep(self.api_delay)
            
            # SAFETY PROTOCOL: Only GET requests allowed
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            logger.debug(f"Successfully fetched: {endpoint}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            raise
    
    def fetch_all_cards(self) -> List[dict]:
        """
        Fetch all cards from Metabase.
        
        🚨 SAFETY: Read-only GET request to /api/card endpoint.
        
        Returns:
            List of all card entries
        """
        logger.info("Fetching all cards from Metabase...")
        
        try:
            cards = self._make_api_request('/api/card')
            logger.info(f"Retrieved {len(cards)} total cards")
            return cards
            
        except Exception as e:
            logger.error(f"Failed to fetch cards: {e}")
            raise
    
    def extract_recent_card_ids(self, cards: List[dict]) -> Dict[int, dict]:
        """
        Extract recently USED card IDs based on actual usage indicators only.
        
        IMPORTANT: Must fetch detailed card info since basic list doesn't include usage fields.
        Excludes 'updated_at' to avoid false positives from system upgrades.
        Uses only: last_query_start, dashboard_count, and parameter_usage_count.
        
        Args:
            cards: List of card entries from /api/card (basic info only)
            
        Returns:
            Dictionary mapping card_id to card info with activity metrics
        """
        logger.info("Extracting recently USED card IDs...")
        logger.info("📋 Criteria: last_query_start >= 12 months ago OR dashboard_count >= 1")
        logger.info("⚠️  Ignoring 'updated_at' to avoid false positives from system upgrades")
        logger.info("🔍 Note: Must fetch detailed info for each card to get usage data")
        
        recent_cards = {}
        processed_count = 0
        
        for card in cards:
            card_id = card.get('id')
            if not card_id:
                continue
                
            # Skip archived cards
            if card.get('archived', False):
                continue
            
            processed_count += 1
            if processed_count % 100 == 0:
                logger.info(f"Processed {processed_count}/{len(cards)} cards...")
            
            # Fetch detailed card info to get usage data
            try:
                detailed_card = self.fetch_card_details(card_id)
                if not detailed_card:
                    continue
                
                # Extract usage indicators from detailed card
                last_query_start = detailed_card.get('last_query_start')
                dashboard_count = detailed_card.get('dashboard_count', 0)
                parameter_usage_count = detailed_card.get('parameter_usage_count', 0)
                
                # Determine if this card has been actually USED recently
                is_recently_used = False
                activity_score = 0
                
                # PRIMARY CRITERION: Check if last queried recently (actual usage)
                if last_query_start:
                    try:
                        # Parse timestamp (assuming ISO format)
                        from datetime import datetime
                        query_time = datetime.fromisoformat(last_query_start.replace('Z', '+00:00'))
                        
                        # FIX: Make twelve_months_ago timezone-aware for proper comparison
                        twelve_months_ago_aware = self.twelve_months_ago.replace(tzinfo=query_time.tzinfo)
                        
                        if query_time >= twelve_months_ago_aware:
                            is_recently_used = True
                            activity_score += 10
                            logger.debug(f"Card {card_id} last queried: {last_query_start}")
                    except Exception as e:
                        logger.warning(f"Could not parse last_query_start for card {card_id}: {e}")
                        pass
                
                # SECONDARY CRITERIA: Dashboard usage and parameter usage indicate active use
                if dashboard_count > 0:
                    activity_score += min(dashboard_count, 5)  # Max 5 points for dashboard usage
                    # If it's on dashboards, it's likely being viewed
                    is_recently_used = True  # Any dashboard usage counts as recent use
                
                if parameter_usage_count > 0:
                    activity_score += min(parameter_usage_count, 3)  # Max 3 points for parameter usage
                
                # Only include cards that have actual usage indicators
                if is_recently_used and activity_score > 0:
                    recent_cards[card_id] = {
                        'activity_score': activity_score,
                        'last_query_start': last_query_start,
                        'dashboard_count': dashboard_count,
                        'parameter_usage_count': parameter_usage_count,
                        'name': detailed_card.get('name', 'Unknown')
                    }
                    
            except Exception as e:
                logger.warning(f"Failed to fetch details for card {card_id}: {e}")
                continue
        
        logger.info(f"Found {len(recent_cards)} recently active cards out of {processed_count} processed")
        
        # Log top active reports
        if recent_cards:
            top_active = sorted(recent_cards.items(), key=lambda x: x[1]['activity_score'], reverse=True)[:10]
            logger.info("Top 10 most active reports:")
            for card_id, info in top_active:
                logger.info(f"  Card ID {card_id}: {info['name'][:50]}... (score: {info['activity_score']})")
        
        return recent_cards
    
    def load_exclusion_list(self, previous_results_file: str) -> Set[int]:
        """
        Load previously analyzed report IDs to exclude from processing.
        
        Args:
            previous_results_file: Path to the Excel file with previous results
            
        Returns:
            Set of report IDs to exclude
        """
        logger.info(f"Loading exclusion list from: {previous_results_file}")
        
        try:
            df = pd.read_excel(previous_results_file)
            
            if 'report_id' not in df.columns:
                raise ValueError("Previous results file missing 'report_id' column")
            
            exclusion_set = set(df['report_id'].tolist())
            logger.info(f"Loaded {len(exclusion_set)} report IDs to exclude from processing")
            return exclusion_set
            
        except Exception as e:
            logger.error(f"Failed to load exclusion list: {e}")
            raise
    
    def fetch_collections_mapping(self) -> Dict[int, str]:
        """
        Fetch all collections and create ID to name mapping.
        
        🚨 SAFETY: Read-only GET request to /api/collection endpoint.
        
        Returns:
            Dictionary mapping collection_id to collection_name
        """
        logger.info("Fetching collections mapping...")
        
        try:
            collections = self._make_api_request('/api/collection')
            
            # Create mapping including root collection (ID = None becomes 0)
            collections_map = {0: "Root Collection"}  # Default for null collection_id
            
            for collection in collections:
                coll_id = collection.get('id')
                coll_name = collection.get('name', 'Unknown Collection')
                
                if coll_id is not None:
                    collections_map[coll_id] = coll_name
            
            logger.info(f"Created mapping for {len(collections_map)} collections")
            return collections_map
            
        except Exception as e:
            logger.error(f"Failed to fetch collections: {e}")
            raise
    
    def fetch_card_details(self, card_id: int) -> Optional[dict]:
        """
        Fetch detailed information for a specific card/report.
        
        🚨 SAFETY: Read-only GET request to /api/card/:id endpoint.
        
        Args:
            card_id: The ID of the card to fetch
            
        Returns:
            Card details dictionary or None if not found/error
        """
        try:
            card_details = self._make_api_request(f'/api/card/{card_id}')
            return card_details
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Card {card_id} not found (404)")
                return None
            logger.error(f"HTTP error fetching card {card_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching card {card_id}: {e}")
            return None
    
    def process_target_reports(self, 
                             target_card_ids: Dict[int, dict], 
                             collections_map: Dict[int, str]) -> pd.DataFrame:
        """
        Process the target list of card IDs and fetch their full details.
        
        Args:
            target_card_ids: Dictionary mapping card_id to activity info
            collections_map: Dictionary mapping collection_id to collection_name
            
        Returns:
            DataFrame with processed report details
        """
        logger.info(f"Processing {len(target_card_ids)} target reports...")
        
        processed_reports = []
        failed_count = 0
        skipped_non_sql = 0
        
        for i, (card_id, activity_info) in enumerate(target_card_ids.items(), 1):
            logger.info(f"Processing card {card_id} ({i}/{len(target_card_ids)})")
            
            # Fetch card details
            card_details = self.fetch_card_details(card_id)
            
            if card_details is None:
                failed_count += 1
                continue
            
            # Filter for native SQL queries only
            query_type = card_details.get('query_type')
            if query_type != 'native':
                logger.debug(f"Skipping card {card_id}: not a native SQL query (type: {query_type})")
                skipped_non_sql += 1
                continue
            
            # Extract relevant information
            report_data = {
                'report_id': card_id,
                'report_name': card_details.get('name', 'Unknown'),
                'description': card_details.get('description', ''),
                'sql_query': card_details.get('dataset_query', {}).get('native', {}).get('query', ''),
                'collection_id': card_details.get('collection_id', 0),
                'collection_name': collections_map.get(card_details.get('collection_id', 0), 'Unknown Collection'),
                'created_at': card_details.get('created_at'),
                'updated_at': card_details.get('updated_at'),
                'activity_score': activity_info['activity_score'],
                'last_query_start': activity_info['last_query_start'],
                'dashboard_count': activity_info['dashboard_count'],
                'parameter_usage_count': activity_info['parameter_usage_count']
            }
            
            processed_reports.append(report_data)
        
        logger.info(f"Processing complete:")
        logger.info(f"  - Successfully processed: {len(processed_reports)} reports")
        logger.info(f"  - Failed to fetch: {failed_count} reports")
        logger.info(f"  - Skipped non-SQL: {skipped_non_sql} reports")
        
        return pd.DataFrame(processed_reports)
    
    def run_analysis(self, previous_results_file: str) -> pd.DataFrame:
        """
        Run the complete analysis to identify and fetch recently viewed reports.
        
        Args:
            previous_results_file: Path to Excel file with previously analyzed reports
            
        Returns:
            DataFrame with new report details
        """
        logger.info("🚀 Starting Recent Reports Analysis")
        logger.info("🚨 Operating under READ-ONLY safety protocol")
        
        try:
            # Step 1: Fetch all cards
            all_cards = self.fetch_all_cards()
            
            # Step 2: Extract recently active card IDs with activity info
            recent_cards_with_activity = self.extract_recent_card_ids(all_cards)
            
            # Step 3: Load exclusion list
            exclusion_set = self.load_exclusion_list(previous_results_file)
            
            # Step 4: Filter target list
            target_cards = {
                card_id: activity_info for card_id, activity_info in recent_cards_with_activity.items()
                if card_id not in exclusion_set
            }
            
            logger.info(f"Target analysis list: {len(target_cards)} new reports to process")
            
            if not target_cards:
                logger.warning("No new reports to process!")
                return pd.DataFrame()
            
            # Step 5: Fetch collections mapping
            collections_map = self.fetch_collections_mapping()
            
            # Step 6: Process target reports
            results_df = self.process_target_reports(target_cards, collections_map)
            
            logger.info("✅ Analysis completed successfully")
            return results_df
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            raise


def get_secure_input(prompt: str, is_password: bool = False) -> str:
    """Get secure input from user with proper handling."""
    if is_password:
        import getpass
        return getpass.getpass(prompt)
    else:
        return input(prompt).strip()


def main():
    """Main execution function."""
    print("🚀 Metabase Recent Reports Fetcher")
    print("🚨 SAFETY PROTOCOL: READ-ONLY operations only")
    print("-" * 50)
    
    # Load environment variables
    load_dotenv('metabase_config.env')
    
    # Configuration
    previous_results_file = "metabase_reports_detailed_20250731_122354.xlsx"
    
    # Check if previous results file exists
    if not Path(previous_results_file).exists():
        logger.error(f"Previous results file not found: {previous_results_file}")
        sys.exit(1)
    
    try:
        # Get Metabase connection details from environment
        base_url = os.getenv('METABASE_BASE_URL')
        api_key = os.getenv('METABASE_API_KEY')
        
        if not base_url or not api_key:
            logger.error("METABASE_BASE_URL and METABASE_API_KEY must be set in metabase_config.env")
            sys.exit(1)
        
        print(f"📡 Connecting to: {base_url}")
        print("🔑 Using API key from environment file")
        
        # Initialize fetcher
        fetcher = MetabaseRecentReportsFetcher(base_url, api_key)
        
        # Run analysis
        results_df = fetcher.run_analysis(previous_results_file)
        
        # Save results
        if not results_df.empty:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"recent_metabase_reports_{timestamp}.xlsx"
            
            results_df.to_excel(output_file, index=False)
            logger.info(f"💾 Results saved to: {output_file}")
            
            # Display summary
            print(f"\n📊 ANALYSIS SUMMARY")
            print(f"   • New reports found: {len(results_df)}")
            print(f"   • Total activity score: {results_df['activity_score'].sum()}")
            print(f"   • Output file: {output_file}")
            
            # Show top active new reports
            if len(results_df) > 0:
                print(f"\n🔥 TOP 5 MOST ACTIVE NEW REPORTS:")
                top_reports = results_df.nlargest(5, 'activity_score')
                for _, report in top_reports.iterrows():
                    print(f"   • {report['report_name'][:50]}... (score: {report['activity_score']})")
        else:
            logger.info("No new reports found to process")
    
    except KeyboardInterrupt:
        logger.info("Analysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 