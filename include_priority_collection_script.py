#!/usr/bin/env python3
"""
Priority Collection 428 Processor
Include collection 428 reports regardless of previous processing status
"""

import pandas as pd
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

def process_priority_collection_428():
    """Process collection 428 reports regardless of previous processing."""
    
    load_dotenv('metabase_config.env')
    
    base_url = os.getenv('METABASE_BASE_URL')
    api_key = os.getenv('METABASE_API_KEY')
    
    session = requests.Session()
    session.headers.update({
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    })
    
    print("🎯 PRIORITY COLLECTION 428 PROCESSOR")
    print("Processing collection 428 regardless of previous analysis")
    print("=" * 60)
    
    try:
        # Get collections mapping
        print("Getting collections mapping...")
        collections = session.get(f"{base_url}/api/collection").json()
        collections_map = {0: "Root Collection"}
        for collection in collections:
            coll_id = collection.get('id')
            if coll_id is not None:
                collections_map[coll_id] = collection.get('name', 'Unknown Collection')
        
        # Get all cards and filter for collection 428
        print("Getting all cards from collection 428...")
        all_cards = session.get(f"{base_url}/api/card").json()
        collection_428_cards = [card for card in all_cards if card.get('collection_id') == 428]
        
        print(f"Found {len(collection_428_cards)} cards in collection 428")
        
        # Process each card
        processed_reports = []
        twelve_months_ago = datetime.now() - timedelta(days=365)
        
        for i, card in enumerate(collection_428_cards, 1):
            card_id = card.get('id')
            print(f"Processing card {card_id} ({i}/{len(collection_428_cards)})")
            
            if card.get('archived', False):
                print(f"  Skipping archived card {card_id}")
                continue
            
            # Get detailed card info
            time.sleep(0.5)  # Rate limiting
            detail_response = session.get(f"{base_url}/api/card/{card_id}")
            
            if detail_response.status_code != 200:
                print(f"  Failed to get details for card {card_id}")
                continue
                
            detailed = detail_response.json()
            
            # Only process native SQL queries
            if detailed.get('query_type') != 'native':
                print(f"  Skipping non-native query {card_id}")
                continue
            
            # Calculate activity score
            last_query_start = detailed.get('last_query_start')
            dashboard_count = detailed.get('dashboard_count', 0)
            parameter_usage_count = detailed.get('parameter_usage_count', 0)
            
            activity_score = 0
            is_recently_used = False
            
            if last_query_start:
                try:
                    query_time = datetime.fromisoformat(last_query_start.replace('Z', '+00:00'))
                    twelve_months_ago_aware = twelve_months_ago.replace(tzinfo=query_time.tzinfo)
                    
                    if query_time >= twelve_months_ago_aware:
                        is_recently_used = True
                        activity_score += 10
                except:
                    pass
            
            if dashboard_count > 0:
                activity_score += min(dashboard_count, 5)
                is_recently_used = True
            
            if parameter_usage_count > 0:
                activity_score += min(parameter_usage_count, 3)
            
            # Include ALL collection 428 reports (regardless of activity)
            # But flag the active ones
            collection_id = detailed.get('collection_id', 0)
            report_data = {
                'report_id': card_id,
                'report_name': detailed.get('name', 'Unknown'),
                'description': detailed.get('description', ''),
                'sql_query': detailed.get('dataset_query', {}).get('native', {}).get('query', ''),
                'collection_id': collection_id,
                'collection_name': collections_map.get(collection_id, 'Unknown Collection'),
                'created_at': detailed.get('created_at'),
                'updated_at': detailed.get('updated_at'),
                'activity_score': activity_score,
                'last_query_start': last_query_start,
                'dashboard_count': dashboard_count,
                'parameter_usage_count': parameter_usage_count,
                'is_priority_collection': True,
                'is_recently_active': is_recently_used and activity_score > 0
            }
            
            processed_reports.append(report_data)
            print(f"  ✅ Processed: {detailed.get('name', 'Unknown')[:40]}... (score: {activity_score})")
        
        # Create DataFrame and save
        if processed_reports:
            df = pd.DataFrame(processed_reports)
            
            # Sort by activity score descending
            df_sorted = df.sort_values('activity_score', ascending=False)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"PRIORITY_collection_428_reports_{timestamp}.xlsx"
            
            df_sorted.to_excel(output_file, index=False)
            
            print(f"\n📊 COLLECTION 428 SUMMARY")
            print(f"   • Total reports processed: {len(df)}")
            print(f"   • Recently active reports: {len(df[df['is_recently_active']])}")
            print(f"   • Total activity score: {df['activity_score'].sum()}")
            print(f"   • Output file: {output_file}")
            
            # Show top reports
            print(f"\n🔥 TOP 10 COLLECTION 428 REPORTS:")
            top_reports = df_sorted.head(10)
            for i, (_, report) in enumerate(top_reports.iterrows(), 1):
                active_flag = "🔥" if report['is_recently_active'] else "📄"
                print(f"{i:2d}. {active_flag} {report['report_name'][:55]}... (score: {report['activity_score']})")
                
            return df_sorted
        else:
            print("No reports found to process")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    result_df = process_priority_collection_428()
    if not result_df.empty:
        print(f"\n✅ Successfully processed {len(result_df)} reports from your priority collection!")
        print("These reports are now ready for business context generation.")
    else:
        print("❌ No reports were processed.") 