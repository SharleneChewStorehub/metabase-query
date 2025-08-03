#!/usr/bin/env python3
"""
Priority Collections Analysis - Find missed reports in key business collections
🚨 SAFETY: READ-ONLY operations only
"""

import requests
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
import time

class PriorityCollectionsAnalyzer:
    """Analyze priority collections to find missed active reports."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        })
        self.api_delay = float(os.getenv('API_DELAY_SECONDS', '0.5'))
        self.twelve_months_ago = datetime.now() - timedelta(days=365)
        
        # Priority collections based on user requirements
        self.priority_collections = {
            238: "Sales (Main)",
            428: "BI x Data Analyst (Sub of Sales)",
            630: "IR-20240927", 
            7: "Product Team",
            40: "For Finance",
            222: "CEO Office"
        }
        
    def _make_api_request(self, endpoint: str) -> dict:
        """Make a safe GET request."""
        time.sleep(self.api_delay)
        response = self.session.get(f"{self.base_url}{endpoint}")
        response.raise_for_status()
        return response.json()
    
    def get_all_collections(self) -> dict:
        """Get all collections and create a mapping."""
        collections = self._make_api_request('/api/collection')
        collections_map = {0: "Root Collection"}
        
        for collection in collections:
            coll_id = collection.get('id')
            if coll_id is not None:
                collections_map[coll_id] = collection.get('name', 'Unknown Collection')
        
        return collections_map
    
    def find_subcollections(self, parent_id: int, all_collections_data: list) -> list:
        """Find all subcollections under a parent collection."""
        subcollections = []
        
        for collection in all_collections_data:
            location = collection.get('location', '')
            # Check if this collection is under the parent
            if f'/{parent_id}/' in location or location == f'/{parent_id}':
                subcollections.append({
                    'id': collection['id'],
                    'name': collection['name'],
                    'location': location
                })
        
        return subcollections
    
    def analyze_collection_cards(self, collection_id: int, collection_name: str, all_cards: list) -> dict:
        """Analyze cards in a specific collection."""
        collection_cards = [card for card in all_cards if card.get('collection_id') == collection_id]
        
        if not collection_cards:
            return {
                'collection_id': collection_id,
                'collection_name': collection_name,
                'total_cards': 0,
                'active_cards': [],
                'summary': f"No cards found in {collection_name}"
            }
        
        active_cards = []
        
        for card in collection_cards:
            card_id = card.get('id')
            if not card_id or card.get('archived', False):
                continue
            
            # Get detailed card info for usage analysis
            try:
                detailed_card = self._make_api_request(f'/api/card/{card_id}')
                
                # Fixed timezone-aware activity scoring
                activity_score, is_recently_used = self.calculate_activity_score(detailed_card)
                
                if is_recently_used and activity_score > 0:
                    active_cards.append({
                        'card_id': card_id,
                        'name': detailed_card.get('name', 'Unknown'),
                        'last_query_start': detailed_card.get('last_query_start'),
                        'dashboard_count': detailed_card.get('dashboard_count', 0),
                        'activity_score': activity_score,
                        'query_type': detailed_card.get('query_type')
                    })
                    
            except Exception as e:
                print(f"Warning: Could not analyze card {card_id}: {e}")
                continue
        
        return {
            'collection_id': collection_id,
            'collection_name': collection_name,
            'total_cards': len(collection_cards),
            'active_cards': active_cards,
            'summary': f"{len(active_cards)} active cards out of {len(collection_cards)} total"
        }
    
    def calculate_activity_score(self, detailed_card: dict) -> tuple:
        """Calculate activity score with fixed timezone handling."""
        activity_score = 0
        is_recently_used = False
        
        last_query_start = detailed_card.get('last_query_start')
        dashboard_count = detailed_card.get('dashboard_count', 0)
        parameter_usage_count = detailed_card.get('parameter_usage_count', 0)
        
        # PRIMARY CRITERION: Check if last queried recently (FIXED timezone handling)
        if last_query_start:
            try:
                query_time = datetime.fromisoformat(last_query_start.replace('Z', '+00:00'))
                # FIX: Make twelve_months_ago timezone-aware for proper comparison
                twelve_months_ago_aware = self.twelve_months_ago.replace(tzinfo=query_time.tzinfo)
                
                if query_time >= twelve_months_ago_aware:
                    is_recently_used = True
                    activity_score += 10
            except Exception:
                pass
        
        # SECONDARY CRITERIA: Dashboard and parameter usage
        if dashboard_count > 0:
            activity_score += min(dashboard_count, 5)
            is_recently_used = True
        
        if parameter_usage_count > 0:
            activity_score += min(parameter_usage_count, 3)
        
        return activity_score, is_recently_used
    
    def check_against_existing_results(self, active_cards: list) -> dict:
        """Check which active cards are missing from our existing results."""
        try:
            # Load previous results
            previous_df = pd.read_excel('metabase_reports_detailed_20250731_122354.xlsx')
            previous_ids = set(previous_df['report_id'].tolist())
            
            # Load recent results  
            recent_df = pd.read_excel('recent_metabase_reports_20250803_024553.xlsx')
            recent_ids = set(recent_df['report_id'].tolist())
            
            total_processed = previous_ids.union(recent_ids)
            
            missing_cards = []
            for card in active_cards:
                if card['card_id'] not in total_processed:
                    missing_cards.append(card)
            
            return {
                'total_active': len(active_cards),
                'in_previous': len([c for c in active_cards if c['card_id'] in previous_ids]),
                'in_recent': len([c for c in active_cards if c['card_id'] in recent_ids]),
                'missing_from_both': len(missing_cards),
                'missing_cards': missing_cards
            }
            
        except Exception as e:
            print(f"Warning: Could not check against existing results: {e}")
            return {'error': str(e)}
    
    def run_priority_analysis(self):
        """Run comprehensive analysis of all priority collections."""
        print("🎯 PRIORITY COLLECTIONS ANALYSIS")
        print("=" * 60)
        print("Analyzing collections with FIXED timezone handling")
        print(f"Looking for activity since: {self.twelve_months_ago.strftime('%Y-%m-%d')}")
        
        # Get all collections data
        print("\n📋 Fetching collections and cards data...")
        all_collections_response = self._make_api_request('/api/collection')
        all_cards = self._make_api_request('/api/card')
        collections_map = self.get_all_collections()
        
        print(f"Total collections: {len(all_collections_response)}")
        print(f"Total cards: {len(all_cards)}")
        
        all_results = []
        all_missing_cards = []
        
        # Analyze each priority collection
        for collection_id, description in self.priority_collections.items():
            print(f"\n🔍 ANALYZING: {description} (ID: {collection_id})")
            print("-" * 50)
            
            # Analyze main collection
            main_result = self.analyze_collection_cards(collection_id, description, all_cards)
            all_results.append(main_result)
            
            print(f"Main collection: {main_result['summary']}")
            
            # For Sales (238) and Product Team (7), also check subcollections
            if collection_id in [238, 7]:
                subcollections = self.find_subcollections(collection_id, all_collections_response)
                print(f"Found {len(subcollections)} subcollections")
                
                for subcoll in subcollections:
                    sub_result = self.analyze_collection_cards(
                        subcoll['id'], 
                        f"{subcoll['name']} (Sub of {description})", 
                        all_cards
                    )
                    all_results.append(sub_result)
                    print(f"  └─ {subcoll['name']}: {sub_result['summary']}")
            
            # Check against existing results
            if main_result['active_cards']:
                missing_analysis = self.check_against_existing_results(main_result['active_cards'])
                if 'missing_cards' in missing_analysis:
                    all_missing_cards.extend(missing_analysis['missing_cards'])
                    
                    if missing_analysis['missing_from_both'] > 0:
                        print(f"🚨 MISSING: {missing_analysis['missing_from_both']} active cards not in any previous analysis!")
        
        # Summary report
        print(f"\n📊 OVERALL SUMMARY")
        print("=" * 60)
        
        total_active = sum(len(result['active_cards']) for result in all_results)
        total_missing = len(all_missing_cards)
        
        print(f"Total active cards found in priority collections: {total_active}")
        print(f"Cards missing from ALL previous analyses: {total_missing}")
        
        if total_missing > 0:
            print(f"\n🔥 TOP MISSING ACTIVE CARDS:")
            # Sort by activity score
            sorted_missing = sorted(all_missing_cards, key=lambda x: x['activity_score'], reverse=True)
            for i, card in enumerate(sorted_missing[:10]):
                print(f"{i+1}. {card['name'][:60]}...")
                print(f"   ID: {card['card_id']} | Score: {card['activity_score']} | Last query: {card['last_query_start']}")
        
        # Save missing cards to file for further processing
        if all_missing_cards:
            missing_df = pd.DataFrame(all_missing_cards)
            output_file = f"MISSING_priority_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            missing_df.to_excel(output_file, index=False)
            print(f"\n💾 Missing cards saved to: {output_file}")
        
        return all_results, all_missing_cards

def main():
    load_dotenv('metabase_config.env')
    
    base_url = os.getenv('METABASE_BASE_URL')
    api_key = os.getenv('METABASE_API_KEY')
    
    if not base_url or not api_key:
        print("❌ Missing environment variables")
        return
    
    analyzer = PriorityCollectionsAnalyzer(base_url, api_key)
    results, missing_cards = analyzer.run_priority_analysis()
    
    if missing_cards:
        print(f"\n✅ Found {len(missing_cards)} previously missed active reports!")
        print("These should be added to your business context generation pipeline.")
    else:
        print("\n✅ All active reports in priority collections have been captured!")

if __name__ == "__main__":
    main() 