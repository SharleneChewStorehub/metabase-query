#!/usr/bin/env python3
"""
Script to add usage information to the existing 1.5K reports with business context.

This script:
1. Reads the FINAL_METABASE_REPORTS_WITH_BUSINESS_CONTEXT_20250801.xlsx file (1.5K reports)
2. Fetches usage information from Metabase API for each report 
3. Adds usage columns: activity_score, last_query_start, dashboard_count, parameter_usage_count, updated_at
4. Saves the enriched data to a new Excel file

SAFETY: Uses only READ-ONLY GET requests to Metabase API (/api/card/{id})
"""

import pandas as pd
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('usage_enrichment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UsageEnrichmentProcessor:
    """Processor to add usage information to existing reports with business context."""
    
    def __init__(self, config_file: str = "metabase_config.env"):
        """Initialize the processor with Metabase configuration."""
        self.config_file = Path(config_file)
        self.base_url = None
        self.api_key = None
        self.session = None
        self.twelve_months_ago = datetime.now() - timedelta(days=365)
        self.api_delay = 0.2  # Rate limiting
        self.request_timeout = 30
        
        # Load Metabase configuration
        self._load_config()
        self._setup_session()
        
    def _load_config(self):
        """Load Metabase configuration from environment file."""
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"Configuration file '{self.config_file}' not found. "
                f"Please run 'python setup_metabase_config.py' to create it."
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
            self.api_delay = float(os.getenv('API_DELAY_SECONDS', '0.2'))
            self.request_timeout = int(os.getenv('REQUEST_TIMEOUT_SECONDS', '30'))
        except (ValueError, TypeError):
            logger.warning("Invalid API settings in config, using defaults")
            self.api_delay = 0.2
            self.request_timeout = 30
        
        logger.info(f"✅ Configuration loaded from {self.config_file}")
        logger.info(f"📍 Metabase URL: {self.base_url}")
        logger.info(f"⏱️  API delay: {self.api_delay}s, Timeout: {self.request_timeout}s")
    
    def _setup_session(self):
        """Setup requests session with API key authentication."""
        self.session = requests.Session()
        
        # Set up API key authentication
        self.session.headers.update({
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'UsageEnrichmentProcessor/1.0 (READ-ONLY)'
        })
        
        # Set timeout for all requests
        self.session.timeout = self.request_timeout
        
        logger.info("✅ Session configured with API key authentication")
    
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
    
    def _make_api_request(self, endpoint: str, params: dict = None) -> dict:
        """
        Make a safe GET request to Metabase API.
        
        🚨 SAFETY: Only GET requests allowed - READ-ONLY operations.
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            # SAFETY PROTOCOL: Only GET requests allowed
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {e}")
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
    
    def calculate_activity_score(self, detailed_card: dict) -> tuple:
        """
        Calculate activity score using the same algorithm as COMPLETE file.
        
        Args:
            detailed_card: Card details from Metabase API
            
        Returns:
            Tuple of (activity_score, is_recently_used)
        """
        activity_score = 0
        is_recently_used = False
        
        last_query_start = detailed_card.get('last_query_start')
        dashboard_count = detailed_card.get('dashboard_count', 0)
        parameter_usage_count = detailed_card.get('parameter_usage_count', 0)
        
        # PRIMARY CRITERION: Check if last queried recently (FIXED timezone handling)
        if last_query_start:
            try:
                query_time = datetime.fromisoformat(last_query_start.replace('Z', '+00:00'))
                # Make twelve_months_ago timezone-aware for proper comparison
                twelve_months_ago_aware = self.twelve_months_ago.replace(tzinfo=query_time.tzinfo)
                
                if query_time >= twelve_months_ago_aware:
                    is_recently_used = True
                    activity_score += 10
                    logger.debug(f"Card has recent query activity: {last_query_start}")
            except Exception as e:
                logger.warning(f"Could not parse last_query_start: {e}")
                pass
        
        # SECONDARY CRITERIA: Dashboard and parameter usage
        if dashboard_count > 0:
            activity_score += min(dashboard_count, 5)  # Max 5 points
            is_recently_used = True  # Any dashboard usage counts as recent use
        
        if parameter_usage_count > 0:
            activity_score += min(parameter_usage_count, 3)  # Max 3 points
        
        return activity_score, is_recently_used
    
    def load_existing_reports(self, file_path: str) -> pd.DataFrame:
        """
        Load the existing reports with business context.
        
        Args:
            file_path: Path to the Excel file with existing reports
            
        Returns:
            DataFrame with existing report data
        """
        try:
            logger.info(f"Loading existing reports from {file_path}...")
            df = pd.read_excel(file_path)
            logger.info(f"✅ Loaded {len(df)} existing reports")
            
            # Verify required columns exist
            if 'metabase_report_id' not in df.columns:
                raise ValueError("metabase_report_id column not found in the file")
            
            logger.info(f"📊 Using metabase_report_id column for API calls")
            logger.info(f"📊 Sample IDs: {df['metabase_report_id'].head().tolist()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load existing reports: {e}")
            raise
    
    def enrich_reports_with_usage(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich existing reports with usage information from Metabase API.
        
        Args:
            df: DataFrame with existing report data
            
        Returns:
            DataFrame enriched with usage columns
        """
        logger.info(f"Starting usage enrichment for {len(df)} reports...")
        
        # Initialize new columns
        df['activity_score'] = 0
        df['last_query_start'] = None
        df['dashboard_count'] = 0
        df['parameter_usage_count'] = 0
        df['updated_at'] = None
        df['is_recently_used'] = False
        df['usage_fetch_status'] = 'pending'
        
        total_reports = len(df)
        processed_count = 0
        success_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            processed_count += 1
            card_id = row['metabase_report_id']
            
            if processed_count % 50 == 0:
                logger.info(f"Progress: {processed_count}/{total_reports} reports processed "
                           f"({success_count} successful, {error_count} errors)")
            
            try:
                # Fetch detailed card information
                logger.debug(f"Fetching usage data for card {card_id}")
                detailed_card = self.fetch_card_details(card_id)
                
                if detailed_card:
                    # Calculate activity score
                    activity_score, is_recently_used = self.calculate_activity_score(detailed_card)
                    
                    # Update the DataFrame
                    df.at[index, 'activity_score'] = activity_score
                    df.at[index, 'last_query_start'] = detailed_card.get('last_query_start')
                    df.at[index, 'dashboard_count'] = detailed_card.get('dashboard_count', 0)
                    df.at[index, 'parameter_usage_count'] = detailed_card.get('parameter_usage_count', 0)
                    df.at[index, 'updated_at'] = detailed_card.get('updated_at')
                    df.at[index, 'is_recently_used'] = is_recently_used
                    df.at[index, 'usage_fetch_status'] = 'success'
                    
                    success_count += 1
                    
                    logger.debug(f"✅ Card {card_id}: activity_score={activity_score}, "
                               f"recently_used={is_recently_used}")
                else:
                    df.at[index, 'usage_fetch_status'] = 'not_found'
                    error_count += 1
                    logger.warning(f"❌ Card {card_id}: Not found or inaccessible")
                
                # Rate limiting to be respectful to Metabase API
                time.sleep(self.api_delay)
                
            except Exception as e:
                df.at[index, 'usage_fetch_status'] = f'error: {str(e)[:100]}'
                error_count += 1
                logger.error(f"❌ Error processing card {card_id}: {e}")
                continue
        
        logger.info(f"✅ Usage enrichment completed!")
        logger.info(f"📊 Final stats: {success_count} successful, {error_count} errors out of {total_reports} total")
        
        return df
    
    def save_enriched_reports(self, df: pd.DataFrame, output_file: str):
        """
        Save the enriched reports to a new Excel file.
        
        Args:
            df: DataFrame with enriched report data
            output_file: Path for the output Excel file
        """
        try:
            logger.info(f"Saving enriched reports to {output_file}...")
            
            # Create a backup timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # If output file already exists, create a backup
            if os.path.exists(output_file):
                backup_file = f"{output_file}_{timestamp}_backup.xlsx"
                logger.info(f"Creating backup: {backup_file}")
                os.rename(output_file, backup_file)
            
            # Save the enriched data
            df.to_excel(output_file, index=False)
            logger.info(f"✅ Successfully saved {len(df)} enriched reports to {output_file}")
            
            # Print summary statistics
            recently_used_count = df['is_recently_used'].sum()
            avg_activity_score = df['activity_score'].mean()
            
            logger.info(f"📊 Summary Statistics:")
            logger.info(f"   - Total reports: {len(df)}")
            logger.info(f"   - Recently used reports: {recently_used_count} ({recently_used_count/len(df)*100:.1f}%)")
            logger.info(f"   - Average activity score: {avg_activity_score:.2f}")
            logger.info(f"   - Reports with dashboard usage: {(df['dashboard_count'] > 0).sum()}")
            logger.info(f"   - Reports with parameter usage: {(df['parameter_usage_count'] > 0).sum()}")
            
        except Exception as e:
            logger.error(f"Failed to save enriched reports: {e}")
            raise

def main():
    """Main execution function."""
    try:
        # Initialize processor
        processor = UsageEnrichmentProcessor()
        
        # Test connection first
        if not processor.test_connection():
            raise Exception("Failed to connect to Metabase API. Please check your configuration.")
        
        # Define file paths
        input_file = "FINAL_METABASE_REPORTS_WITH_BUSINESS_CONTEXT_20250801.xlsx"
        output_file = f"FINAL_METABASE_REPORTS_WITH_USAGE_CONTEXT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Check if input file exists
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Load existing reports
        df = processor.load_existing_reports(input_file)
        
        # Enrich with usage information
        enriched_df = processor.enrich_reports_with_usage(df)
        
        # Save enriched reports
        processor.save_enriched_reports(enriched_df, output_file)
        
        logger.info(f"🎉 Usage enrichment process completed successfully!")
        logger.info(f"📁 Output file: {output_file}")
        
    except Exception as e:
        logger.error(f"❌ Usage enrichment process failed: {e}")
        raise

if __name__ == "__main__":
    main() 