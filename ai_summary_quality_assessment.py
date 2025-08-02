#!/usr/bin/env python3
"""
AI Summary Quality Assessment Tool

A comprehensive Python script to analyze the quality of AI-generated SQL query summaries
by comparing them against human-written report names and original SQL queries.

Author: Senior Business Analyst & Python Developer
"""

import pandas as pd
import numpy as np
import glob
import os
import re
import sys
from pathlib import Path
from typing import Tuple, List, Dict, Any
import warnings

# Suppress pandas warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

class AIQualityAssessor:
    """
    Comprehensive quality assessor for AI-generated SQL query summaries.
    """
    
    def __init__(self):
        self.df = None
        self.assessment_df = None
        self.common_business_terms = {
            'specific_indicators': [
                'cancelled', 'active', 'inactive', 'pending', 'completed', 'failed',
                'premium', 'basic', 'trial', 'free', 'paid', 'subscribed', 'unsubscribed',
                'new', 'returning', 'churned', 'retained', 'converted', 'abandoned',
                'high-value', 'low-value', 'vip', 'enterprise', 'individual',
                'universal', 'targeted', 'seasonal', 'promotional', 'discount',
                'revenue', 'profit', 'cost', 'expense', 'budget', 'forecast'
            ],
            'generic_terms': [
                'analyze', 'track', 'monitor', 'measure', 'calculate', 'determine',
                'performance', 'metrics', 'data', 'information', 'results',
                'insights', 'trends', 'patterns', 'statistics', 'summary'
            ]
        }
    
    def find_excel_file(self) -> str:
        """
        Automatically find the Excel file in the current directory.
        
        Returns:
            str: Path to the Excel file
            
        Raises:
            FileNotFoundError: If no Excel file is found
            ValueError: If multiple Excel files are found
        """
        current_dir = Path.cwd()
        excel_files = list(current_dir.glob("*.xlsx"))
        
        if not excel_files:
            raise FileNotFoundError(
                "❌ No Excel (.xlsx) file found in the current directory. "
                "Please ensure there is exactly one .xlsx file in the project folder."
            )
        
        if len(excel_files) > 1:
            print(f"⚠️  Multiple Excel files found: {[f.name for f in excel_files]}")
            print("📋 Using the first file found...")
        
        excel_file = excel_files[0]
        print(f"📖 Found Excel file: {excel_file.name}")
        return str(excel_file)
    
    def load_data(self) -> pd.DataFrame:
        """
        Load the Excel file into a pandas DataFrame.
        
        Returns:
            pd.DataFrame: Loaded data
        """
        try:
            file_path = self.find_excel_file()
            
            # Try to read all sheets and find the one with the most data
            excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
            
            # Find the sheet with the most rows (likely the main data)
            main_sheet = max(excel_data.keys(), key=lambda x: len(excel_data[x]))
            self.df = excel_data[main_sheet]
            
            print(f"✅ Successfully loaded data from sheet '{main_sheet}'")
            print(f"📏 Dataset shape: {self.df.shape[0]:,} rows × {self.df.shape[1]} columns")
            
            # Display column names for verification
            print(f"📋 Available columns: {list(self.df.columns)}")
            
            return self.df
            
        except Exception as e:
            print(f"❌ Error loading Excel file: {str(e)}")
            sys.exit(1)
    
    def extract_sql_filters(self, sql_query: str) -> List[str]:
        """
        Extract key business filters from SQL WHERE clauses.
        
        Args:
            sql_query (str): The SQL query text
            
        Returns:
            List[str]: List of identified filters
        """
        if pd.isna(sql_query) or not isinstance(sql_query, str):
            return []
        
        filters = []
        sql_lower = sql_query.lower()
        
        # Common filter patterns
        filter_patterns = [
            r"(\w+)\s*=\s*['\"]([^'\"]+)['\"]",  # column = 'value'
            r"(\w+)\s*=\s*(\w+)",  # column = value
            r"(\w+)\s+in\s*\([^)]+\)",  # column IN (...)
            r"(\w+)\s+like\s*['\"]([^'\"]+)['\"]",  # column LIKE 'pattern'
            r"(\w+)\s*>\s*(\d+)",  # column > number
            r"(\w+)\s*<\s*(\d+)",  # column < number
            r"status\s*=\s*['\"]?(\w+)['\"]?",  # status filters
            r"type\s*=\s*['\"]?(\w+)['\"]?",  # type filters
        ]
        
        for pattern in filter_patterns:
            matches = re.findall(pattern, sql_lower)
            for match in matches:
                if isinstance(match, tuple):
                    filter_desc = f"{match[0]} = {match[1] if len(match) > 1 else ''}"
                else:
                    filter_desc = str(match)
                filters.append(filter_desc.strip())
        
        # Look for common business filter keywords
        business_keywords = [
            'cancelled', 'active', 'inactive', 'pending', 'completed',
            'premium', 'basic', 'trial', 'paid', 'free',
            'universal', 'targeted', 'promotional',
            'new', 'returning', 'churned'
        ]
        
        for keyword in business_keywords:
            if keyword in sql_lower:
                filters.append(f"filter: {keyword}")
        
        return list(set(filters))  # Remove duplicates
    
    def calculate_specificity_score(self, report_name: str, business_explanation: str, 
                                   business_purpose: str, sql_filters: List[str]) -> int:
        """
        Calculate specificity score (1-5) based on how specific the AI summary is.
        
        Args:
            report_name (str): Human-written report name
            business_explanation (str): AI's detailed explanation  
            business_purpose (str): AI's high-level purpose
            sql_filters (List[str]): Extracted SQL filters
            
        Returns:
            int: Specificity score (1-5)
        """
        if pd.isna(business_explanation) and pd.isna(business_purpose):
            return 1
        
        # Combine AI text for analysis
        ai_text = f"{str(business_explanation)} {str(business_purpose)}".lower()
        report_name_lower = str(report_name).lower() if not pd.isna(report_name) else ""
        
        score = 1  # Start with lowest score
        
        # Check for specific entity mentions from report name
        if report_name_lower:
            report_words = re.findall(r'\w+', report_name_lower)
            specific_words = [w for w in report_words if len(w) > 3 and 
                            w not in ['report', 'analysis', 'data', 'query']]
            
            matches = sum(1 for word in specific_words if word in ai_text)
            if matches >= len(specific_words) * 0.7:  # 70% of specific words mentioned
                score = max(score, 5)
            elif matches >= len(specific_words) * 0.4:  # 40% mentioned
                score = max(score, 4)
        
        # Check for specific business indicators
        specific_indicators = self.common_business_terms['specific_indicators']
        specific_mentions = sum(1 for term in specific_indicators if term in ai_text)
        
        if specific_mentions >= 3:
            score = max(score, 5)
        elif specific_mentions >= 2:
            score = max(score, 4)
        elif specific_mentions >= 1:
            score = max(score, 3)
        
        # Check for SQL filter mentions
        filter_mentions = 0
        for sql_filter in sql_filters:
            filter_words = re.findall(r'\w+', sql_filter.lower())
            for word in filter_words:
                if len(word) > 3 and word in ai_text:
                    filter_mentions += 1
                    break
        
        if filter_mentions >= len(sql_filters) * 0.8 and len(sql_filters) > 0:
            score = max(score, 5)
        elif filter_mentions >= len(sql_filters) * 0.5 and len(sql_filters) > 0:
            score = max(score, 4)
        
        # Penalize if too generic
        generic_terms = self.common_business_terms['generic_terms']
        generic_count = sum(1 for term in generic_terms if term in ai_text)
        specific_count = sum(1 for term in specific_indicators if term in ai_text)
        
        if generic_count > specific_count * 2 and specific_count > 0:
            score = max(1, score - 1)
        
        return min(5, score)
    
    def calculate_intent_score(self, business_explanation: str, business_purpose: str) -> int:
        """
        Calculate intent score (1-5) based on business vs technical focus.
        
        Args:
            business_explanation (str): AI's detailed explanation
            business_purpose (str): AI's high-level purpose
            
        Returns:
            int: Intent score (1-5)
        """
        if pd.isna(business_explanation) and pd.isna(business_purpose):
            return 1
        
        ai_text = f"{str(business_explanation)} {str(business_purpose)}".lower()
        
        # Business intent indicators
        business_indicators = [
            'business', 'customer', 'revenue', 'profit', 'growth', 'performance',
            'strategy', 'decision', 'insight', 'trend', 'opportunity', 'risk',
            'market', 'segment', 'campaign', 'conversion', 'retention', 'churn',
            'satisfaction', 'engagement', 'acquisition', 'value', 'roi', 'kpi',
            'goal', 'objective', 'target', 'outcome', 'impact', 'success',
            'understand', 'identify', 'discover', 'optimize', 'improve', 'monitor'
        ]
        
        # Technical description indicators  
        technical_indicators = [
            'join', 'cte', 'subquery', 'aggregate', 'group by', 'order by',
            'left join', 'inner join', 'outer join', 'union', 'case when',
            'count', 'sum', 'avg', 'max', 'min', 'distinct', 'partition',
            'window function', 'recursive', 'temporary table', 'index',
            'database', 'table', 'column', 'row', 'field', 'schema',
            'sql', 'query', 'select', 'from', 'where', 'having'
        ]
        
        business_count = sum(1 for term in business_indicators if term in ai_text)
        technical_count = sum(1 for term in technical_indicators if term in ai_text)
        
        total_words = len(ai_text.split())
        business_ratio = business_count / max(total_words, 1)
        technical_ratio = technical_count / max(total_words, 1)
        
        # Score based on business vs technical focus
        if business_ratio > technical_ratio * 2 and business_count >= 3:
            return 5  # Strong business focus
        elif business_ratio > technical_ratio and business_count >= 2:
            return 4  # Good business focus
        elif business_count > 0 and technical_count > 0:
            return 3  # Mixed focus
        elif technical_count > business_count and technical_count >= 2:
            return 2  # Primarily technical
        else:
            return 1  # No clear business intent
    
    def assess_key_levers(self, business_explanation: str, business_purpose: str, 
                         sql_filters: List[str]) -> str:
        """
        Assess if AI identified key business levers from SQL filters.
        
        Args:
            business_explanation (str): AI's detailed explanation
            business_purpose (str): AI's high-level purpose  
            sql_filters (List[str]): Extracted SQL filters
            
        Returns:
            str: 'Yes', 'Partial', or 'No'
        """
        if not sql_filters:
            return "Yes"  # No filters to identify
        
        if pd.isna(business_explanation) and pd.isna(business_purpose):
            return "No"
        
        ai_text = f"{str(business_explanation)} {str(business_purpose)}".lower()
        
        # Count how many filters are mentioned
        mentioned_filters = 0
        for sql_filter in sql_filters:
            filter_words = re.findall(r'\w+', sql_filter.lower())
            filter_mentioned = False
            
            for word in filter_words:
                if len(word) > 3 and word in ai_text:
                    filter_mentioned = True
                    break
            
            if filter_mentioned:
                mentioned_filters += 1
        
        if len(sql_filters) == 0:
            return "Yes"
        
        mention_ratio = mentioned_filters / len(sql_filters)
        
        if mention_ratio >= 0.8:  # 80% or more filters mentioned
            return "Yes"
        elif mention_ratio >= 0.4:  # 40-79% mentioned
            return "Partial"
        else:
            return "No"
    
    def calculate_overall_assessment(self, specificity_score: int, intent_score: int, 
                                   key_levers: str) -> str:
        """
        Calculate overall assessment based on individual scores.
        
        Args:
            specificity_score (int): Specificity score (1-5)
            intent_score (int): Intent score (1-5)
            key_levers (str): Key levers assessment
            
        Returns:
            str: 'Good', 'Average', or 'Poor'
        """
        # Convert key_levers to numeric for calculation
        key_levers_score = {"Yes": 3, "Partial": 2, "No": 1}[key_levers]
        
        # Weight the scores
        weighted_score = (specificity_score * 0.4 + intent_score * 0.4 + key_levers_score * 0.2)
        
        if weighted_score >= 4.0 and specificity_score >= 4 and intent_score >= 4:
            return "Good"
        elif weighted_score >= 2.5:
            return "Average"
        else:
            return "Poor"
    
    def create_justification(self, specificity_score: int, intent_score: int, 
                           key_levers: str, report_name: str) -> str:
        """
        Create a justification for the overall assessment.
        
        Args:
            specificity_score (int): Specificity score
            intent_score (int): Intent score
            key_levers (str): Key levers assessment
            report_name (str): Original report name
            
        Returns:
            str: Justification text
        """
        issues = []
        
        if specificity_score <= 2:
            issues.append("summary is too generic")
        if intent_score <= 2:
            issues.append("focuses on technical details rather than business context")
        if key_levers == "No":
            issues.append("fails to identify key business filters")
        elif key_levers == "Partial":
            issues.append("misses some important business filters")
        
        if not issues:
            return f"Summary effectively captures the business context of '{report_name}' with appropriate specificity and business focus."
        else:
            issue_text = ", ".join(issues)
            return f"Summary has issues: {issue_text} for '{report_name}'."
    
    def assess_single_row(self, row: pd.Series) -> Dict[str, Any]:
        """
        Assess a single row of data.
        
        Args:
            row (pd.Series): Row of data to assess
            
        Returns:
            Dict[str, Any]: Assessment results
        """
        # Extract data with fallback for missing columns
        report_name = row.get('Report Name', '')
        sql_query = row.get('SQL Query', '')
        business_explanation = row.get('Business Explanation', '')
        business_purpose = row.get('Business Purpose', '')
        
        # Extract SQL filters
        sql_filters = self.extract_sql_filters(sql_query)
        
        # Calculate scores
        specificity_score = self.calculate_specificity_score(
            report_name, business_explanation, business_purpose, sql_filters
        )
        
        intent_score = self.calculate_intent_score(business_explanation, business_purpose)
        
        key_levers = self.assess_key_levers(
            business_explanation, business_purpose, sql_filters
        )
        
        overall_assessment = self.calculate_overall_assessment(
            specificity_score, intent_score, key_levers
        )
        
        justification = self.create_justification(
            specificity_score, intent_score, key_levers, report_name
        )
        
        return {
            'Specificity_Score': specificity_score,
            'Intent_Score': intent_score,
            'Key_Levers_Identified': key_levers,
            'Overall_Assessment': overall_assessment,
            'Justification': justification,
            'SQL_Filters_Found': len(sql_filters),
            'SQL_Filters_Detail': '; '.join(sql_filters[:3])  # First 3 for reference
        }
    
    def perform_assessment(self) -> pd.DataFrame:
        """
        Perform quality assessment on all rows.
        
        Returns:
            pd.DataFrame: Assessment results
        """
        print("\n🔍 Starting AI Summary Quality Assessment...")
        print("=" * 70)
        
        # Verify required columns exist
        required_columns = ['Report Name', 'SQL Query', 'Business Explanation', 'Business Purpose']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        
        if missing_columns:
            print(f"⚠️  Warning: Missing columns: {missing_columns}")
            print("📋 Available columns:", list(self.df.columns))
            print("🔄 Proceeding with available columns...")
        
        # Apply assessment to each row
        assessment_results = []
        
        print(f"📊 Processing {len(self.df)} rows...")
        
        for idx, row in self.df.iterrows():
            if idx % 100 == 0:  # Progress indicator
                print(f"   Processed {idx:,} rows...")
            
            result = self.assess_single_row(row)
            assessment_results.append(result)
        
        # Create assessment DataFrame
        self.assessment_df = pd.DataFrame(assessment_results)
        
        # Combine with original data
        result_df = pd.concat([self.df.reset_index(drop=True), self.assessment_df], axis=1)
        
        print(f"✅ Assessment complete! Processed {len(result_df):,} rows")
        return result_df
    
    def generate_summary_analysis(self) -> None:
        """
        Generate and print comprehensive summary analysis.
        """
        if self.assessment_df is None:
            print("❌ No assessment data available. Run perform_assessment() first.")
            return
        
        print("\n" + "="*70)
        print("📈 COMPREHENSIVE SUMMARY ANALYSIS")
        print("="*70)
        
        # Overall distribution
        assessment_counts = self.assessment_df['Overall_Assessment'].value_counts()
        total_rows = len(self.assessment_df)
        
        print(f"\n📊 Overall Quality Distribution ({total_rows:,} total assessments):")
        for assessment, count in assessment_counts.items():
            percentage = (count / total_rows) * 100
            print(f"   {assessment:8s}: {count:4d} ({percentage:5.1f}%)")
        
        # Average scores
        avg_specificity = self.assessment_df['Specificity_Score'].mean()
        avg_intent = self.assessment_df['Intent_Score'].mean()
        
        print(f"\n📊 Average Scores:")
        print(f"   Specificity Score: {avg_specificity:.2f} / 5.00")
        print(f"   Intent Score:      {avg_intent:.2f} / 5.00")
        
        # Key levers analysis
        key_levers_counts = self.assessment_df['Key_Levers_Identified'].value_counts()
        print(f"\n🎯 Key Business Levers Identification:")
        for lever, count in key_levers_counts.items():
            percentage = (count / total_rows) * 100
            print(f"   {lever:8s}: {count:4d} ({percentage:5.1f}%)")
        
        # Score distribution analysis
        print(f"\n📈 Score Distribution Analysis:")
        
        specificity_dist = self.assessment_df['Specificity_Score'].value_counts().sort_index()
        print(f"   Specificity Scores:")
        for score, count in specificity_dist.items():
            percentage = (count / total_rows) * 100
            print(f"     Score {score}: {count:4d} ({percentage:5.1f}%)")
        
        intent_dist = self.assessment_df['Intent_Score'].value_counts().sort_index()
        print(f"   Intent Scores:")
        for score, count in intent_dist.items():
            percentage = (count / total_rows) * 100
            print(f"     Score {score}: {count:4d} ({percentage:5.1f}%)")
        
        # Common failure patterns analysis
        print(f"\n🔍 Common Failure Patterns:")
        
        poor_assessments = self.assessment_df[self.assessment_df['Overall_Assessment'] == 'Poor']
        if len(poor_assessments) > 0:
            # Analyze why assessments are poor
            low_specificity = len(poor_assessments[poor_assessments['Specificity_Score'] <= 2])
            low_intent = len(poor_assessments[poor_assessments['Intent_Score'] <= 2])
            no_key_levers = len(poor_assessments[poor_assessments['Key_Levers_Identified'] == 'No'])
            
            print(f"   Among {len(poor_assessments)} 'Poor' assessments:")
            print(f"     {low_specificity} ({low_specificity/len(poor_assessments)*100:.1f}%) have low specificity (≤2)")
            print(f"     {low_intent} ({low_intent/len(poor_assessments)*100:.1f}%) have low business intent (≤2)")
            print(f"     {no_key_levers} ({no_key_levers/len(poor_assessments)*100:.1f}%) miss key business levers")
        
        # SQL filters analysis
        avg_filters = self.assessment_df['SQL_Filters_Found'].mean()
        print(f"\n⚙️  SQL Analysis:")
        print(f"   Average filters per query: {avg_filters:.1f}")
        
        no_filters = len(self.assessment_df[self.assessment_df['SQL_Filters_Found'] == 0])
        print(f"   Queries with no identifiable filters: {no_filters} ({no_filters/total_rows*100:.1f}%)")
        
        # Recommendations
        print(f"\n💡 Key Recommendations:")
        
        if avg_specificity < 3.0:
            print("   • AI summaries need to be more specific - include entity names and conditions")
        
        if avg_intent < 3.0:
            print("   • AI should focus more on business context rather than technical SQL details")
        
        no_levers_pct = (key_levers_counts.get('No', 0) / total_rows) * 100
        if no_levers_pct > 30:
            print(f"   • AI misses key business filters in {no_levers_pct:.1f}% of cases - improve filter detection")
        
        poor_pct = (assessment_counts.get('Poor', 0) / total_rows) * 100
        if poor_pct > 25:
            print(f"   • {poor_pct:.1f}% of summaries are poor quality - comprehensive AI training needed")
        
        print(f"\n✨ Analysis complete! Assessment data ready for further investigation.")


def main():
    """
    Main execution function.
    """
    try:
        print("🚀 AI Summary Quality Assessment Tool")
        print("="*50)
        
        # Initialize assessor
        assessor = AIQualityAssessor()
        
        # Load data
        df = assessor.load_data()
        
        # Perform assessment
        assessment_df = assessor.perform_assessment()
        
        # Generate summary analysis
        assessor.generate_summary_analysis()
        
        # Save results
        output_file = "ai_summary_assessment_results.xlsx"
        assessment_df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"\n💾 Results saved to: {output_file}")
        
        # Display sample results
        print(f"\n📋 Sample Assessment Results (first 3 rows):")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        sample_cols = ['Report Name', 'Specificity_Score', 'Intent_Score', 
                      'Key_Levers_Identified', 'Overall_Assessment']
        if all(col in assessment_df.columns for col in sample_cols):
            print(assessment_df[sample_cols].head(3).to_string(index=False))
        
        return assessment_df
        
    except Exception as e:
        print(f"💥 Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    result_df = main() 