#!/usr/bin/env python3
"""
Test script to verify usage enrichment works on a small sample.
This helps verify configuration and API access before processing all 1.5K reports.
"""

import pandas as pd
from add_usage_to_final_reports import UsageEnrichmentProcessor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_usage_enrichment():
    """Test the usage enrichment on a small sample."""
    try:
        logger.info("🧪 Testing usage enrichment process...")
        
        # Initialize processor
        processor = UsageEnrichmentProcessor()
        
        # Test connection
        if not processor.test_connection():
            logger.error("❌ Connection test failed")
            return False
        
        # Load the full dataset
        input_file = "FINAL_METABASE_REPORTS_WITH_BUSINESS_CONTEXT_20250801.xlsx"
        df = processor.load_existing_reports(input_file)
        
        # Test on first 5 reports only
        test_df = df.head(5).copy()
        logger.info(f"🧪 Testing with {len(test_df)} sample reports")
        
        # Print the sample report IDs we're testing
        logger.info(f"📊 Testing report IDs: {test_df['metabase_report_id'].tolist()}")
        logger.info(f"📊 Report names: {test_df['report_id'].tolist()}")
        
        # Enrich the sample
        enriched_df = processor.enrich_reports_with_usage(test_df)
        
        # Show results
        logger.info("🧪 Test Results:")
        for _, row in enriched_df.iterrows():
            logger.info(f"   Report {row['metabase_report_id']} ({row['report_id']}): "
                       f"activity_score={row['activity_score']}, "
                       f"recently_used={row['is_recently_used']}, "
                       f"status={row['usage_fetch_status']}")
        
        # Save test results
        test_output = "test_usage_enrichment_results.xlsx"
        enriched_df.to_excel(test_output, index=False)
        logger.info(f"✅ Test results saved to {test_output}")
        
        success_count = (enriched_df['usage_fetch_status'] == 'success').sum()
        logger.info(f"✅ Test completed: {success_count}/{len(test_df)} successful")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_usage_enrichment()
    if success:
        print("\n🎉 Test successful! You can now run the full enrichment with:")
        print("   python3 add_usage_to_final_reports.py")
    else:
        print("\n❌ Test failed. Please check your configuration and try again.") 