#!/usr/bin/env python3
"""
Final Quality Assessment for Metabase Business Context Generation

This script performs a comprehensive quality assessment of the generated business context
for Metabase reports, scoring each entry on semantic clarity, deconstruction accuracy,
and blueprint potential for downstream AI systems.

Author: Senior AI Engineer
Date: 2025-01-31
"""

import pandas as pd
import numpy as np
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
from datetime import datetime

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

class BusinessContextQualityAssessor:
    """
    Comprehensive quality assessment system for business context generation results.
    """
    
    def __init__(self, input_file: str):
        """
        Initialize the quality assessor.
        
        Args:
            input_file (str): Path to the final results Excel file
        """
        self.input_file = Path(input_file)
        self.df: Optional[pd.DataFrame] = None
        self.assessment_results: Optional[pd.DataFrame] = None
        
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
    
    def load_data(self) -> None:
        """Load the final results data from Excel file."""
        print(f"📖 Loading data from: {self.input_file}")
        
        try:
            # Load the Excel file - specifically the sheet with results
            self.df = pd.read_excel(self.input_file, sheet_name='Final_Results_With_Metabase_IDs', engine='openpyxl')
            print(f"✅ Successfully loaded {len(self.df)} records")
            
            # Display column information
            print(f"\n📊 Data Structure:")
            print(f"   Shape: {self.df.shape[0]:,} rows × {self.df.shape[1]} columns")
            print(f"   Columns: {list(self.df.columns)}")
            
            # Check for required columns (using actual column names from the file)
            required_columns = ['original_report_name', 'original_description', 'original_sql_query', 'business_question', 'primary_metrics', 'key_filters']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            
            if missing_columns:
                print(f"⚠️  Warning: Missing expected columns: {missing_columns}")
            else:
                print("✅ All required columns present")
                
        except Exception as e:
            print(f"❌ Error loading data: {str(e)}")
            raise
    
    def assess_semantic_clarity(self, row: pd.Series) -> Tuple[int, str]:
        """
        Assess how well the Business_Question captures the nuance of report_name and description.
        
        Args:
            row (pd.Series): DataFrame row containing the data
            
        Returns:
            Tuple[int, str]: Score (1-5) and explanation
        """
        report_name = str(row.get('original_report_name', '')).strip()
        description = str(row.get('original_description', '')).strip()
        business_question = str(row.get('business_question', '')).strip()
        
        # Handle missing data
        if not business_question or business_question.lower() in ['nan', 'none', '']:
            return 1, "Missing or empty business question"
        
        if not report_name and not description:
            return 2, "No source context available for comparison"
        
        # Combine report name and description for analysis
        source_context = f"{report_name} {description}".lower()
        business_q_lower = business_question.lower()
        
        # Scoring criteria
        score = 1
        reasons = []
        
        # Check for key business terms alignment
        business_terms = ['revenue', 'profit', 'customer', 'user', 'conversion', 'retention', 
                         'growth', 'performance', 'efficiency', 'cost', 'sales', 'marketing',
                         'engagement', 'churn', 'acquisition']
        
        source_business_terms = sum(1 for term in business_terms if term in source_context)
        question_business_terms = sum(1 for term in business_terms if term in business_q_lower)
        
        # Score based on various factors
        if len(business_question) > 20:  # Minimum meaningful length
            score += 1
            
        # Check if business question captures key elements from source
        key_words_from_source = [word for word in source_context.split() 
                               if len(word) > 3 and word.isalpha()][:10]
        captured_concepts = sum(1 for word in key_words_from_source 
                              if word in business_q_lower)
        
        if captured_concepts >= 2:
            score += 1
            reasons.append("captures key concepts from source")
        
        # Check for business context specificity
        if question_business_terms > 0:
            score += 1
            reasons.append("includes business-relevant terms")
        
        # Check for question format and clarity
        question_indicators = ['what', 'how', 'which', 'when', 'where', 'why', '?']
        if any(indicator in business_q_lower for indicator in question_indicators):
            score += 1
            reasons.append("properly formatted as a question")
        
        # Cap at 5
        score = min(5, score)
        
        # Generate explanation
        if score >= 4:
            explanation = f"Excellent clarity - {', '.join(reasons) if reasons else 'captures source nuance well'}"
        elif score == 3:
            explanation = f"Good clarity - {', '.join(reasons) if reasons else 'adequate capture of source context'}"
        elif score == 2:
            explanation = "Basic clarity - minimal alignment with source context"
        else:
            explanation = "Poor clarity - fails to capture source meaning"
        
        return score, explanation
    
    def assess_deconstruction_accuracy(self, row: pd.Series) -> Tuple[int, str]:
        """
        Assess how accurately Primary_Metric(s) and Key_Filters reflect the SQL query logic.
        
        Args:
            row (pd.Series): DataFrame row containing the data
            
        Returns:
            Tuple[int, str]: Score (1-5) and explanation
        """
        sql_query = str(row.get('original_sql_query', '')).strip()
        primary_metrics = str(row.get('primary_metrics', '')).strip()
        key_filters = str(row.get('key_filters', '')).strip()
        
        # Handle missing data
        if not sql_query or sql_query.lower() in ['nan', 'none', '']:
            return 1, "Missing SQL query for analysis"
        
        if not primary_metrics and not key_filters:
            return 1, "Missing both metrics and filters"
        
        sql_lower = sql_query.lower()
        score = 1
        reasons = []
        
        # Analyze SQL components
        has_select = 'select' in sql_lower
        has_from = 'from' in sql_lower
        has_where = 'where' in sql_lower
        has_group_by = 'group by' in sql_lower
        has_having = 'having' in sql_lower
        has_order_by = 'order by' in sql_lower
        
        # Check for aggregation functions in SQL vs Primary Metrics
        sql_aggregations = re.findall(r'\b(count|sum|avg|average|min|max|distinct)\s*\(', sql_lower)
        metrics_lower = primary_metrics.lower()
        
        if primary_metrics and primary_metrics.lower() not in ['nan', 'none', '']:
            score += 1
            
            # Check if metrics align with SQL aggregations
            metric_alignment = 0
            for agg in sql_aggregations:
                if agg in metrics_lower or any(synonym in metrics_lower 
                    for synonym in self._get_metric_synonyms(agg)):
                    metric_alignment += 1
            
            if metric_alignment > 0:
                score += 1
                reasons.append("metrics align with SQL aggregations")
        
        # Check WHERE clause vs Key_Filters
        if key_filters and key_filters.lower() not in ['nan', 'none', '']:
            if has_where:
                # Extract potential filter conditions
                where_clause = self._extract_where_clause(sql_query)
                filter_alignment = self._assess_filter_alignment(where_clause, key_filters)
                
                if filter_alignment > 0.5:  # Good alignment
                    score += 1
                    reasons.append("filters accurately reflect WHERE conditions")
                elif filter_alignment > 0.2:  # Partial alignment
                    reasons.append("partial filter alignment")
            else:
                if len(key_filters) < 20:  # Short filter description might be acceptable
                    reasons.append("minimal filters for simple query")
        
        # Bonus points for comprehensive deconstruction
        if has_group_by and 'group' in (primary_metrics + key_filters).lower():
            score += 1
            reasons.append("captures grouping logic")
        
        # Cap at 5
        score = min(5, score)
        
        # Generate explanation
        if score >= 4:
            explanation = f"Excellent accuracy - {', '.join(reasons) if reasons else 'precise SQL deconstruction'}"
        elif score == 3:
            explanation = f"Good accuracy - {', '.join(reasons) if reasons else 'adequate SQL interpretation'}"
        elif score == 2:
            explanation = "Basic accuracy - partial SQL understanding"
        else:
            explanation = "Poor accuracy - fails to reflect SQL logic"
        
        return score, explanation
    
    def assess_blueprint_potential(self, row: pd.Series) -> Tuple[int, str]:
        """
        Assess how useful this entry is as a blueprint for NL-to-SQL tools.
        
        Args:
            row (pd.Series): DataFrame row containing the data
            
        Returns:
            Tuple[int, str]: Score (1-5) and explanation
        """
        business_question = str(row.get('business_question', '')).strip()
        primary_metrics = str(row.get('primary_metrics', '')).strip()
        key_filters = str(row.get('key_filters', '')).strip()
        sql_query = str(row.get('original_sql_query', '')).strip()
        
        score = 1
        reasons = []
        
        # Check completeness of the blueprint
        completeness_score = 0
        if business_question and business_question.lower() not in ['nan', 'none', '']:
            completeness_score += 1
        if primary_metrics and primary_metrics.lower() not in ['nan', 'none', '']:
            completeness_score += 1
        if key_filters and key_filters.lower() not in ['nan', 'none', '']:
            completeness_score += 1
        if sql_query and sql_query.lower() not in ['nan', 'none', '']:
            completeness_score += 1
        
        if completeness_score >= 3:
            score += 1
            reasons.append("complete blueprint components")
        
        # Check specificity and clarity
        if business_question:
            if len(business_question) > 30 and '?' in business_question:
                score += 1
                reasons.append("specific and well-formed question")
        
        # Check SQL complexity and value
        if sql_query:
            sql_complexity = self._assess_sql_complexity(sql_query)
            if sql_complexity >= 3:  # Medium to high complexity
                score += 1
                reasons.append("valuable SQL pattern complexity")
        
        # Check for business value indicators
        business_value_terms = ['revenue', 'profit', 'customer', 'conversion', 'retention',
                               'growth', 'performance', 'cost', 'efficiency', 'churn']
        
        full_text = f"{business_question} {primary_metrics} {key_filters}".lower()
        business_relevance = sum(1 for term in business_value_terms if term in full_text)
        
        if business_relevance > 0:
            score += 1
            reasons.append("high business relevance")
        
        # Cap at 5
        score = min(5, score)
        
        # Generate explanation
        if score >= 4:
            explanation = f"Excellent blueprint - {', '.join(reasons) if reasons else 'clear, specific, and valuable'}"
        elif score == 3:
            explanation = f"Good blueprint - {', '.join(reasons) if reasons else 'useful for NL-to-SQL training'}"
        elif score == 2:
            explanation = "Basic blueprint - limited training value"
        else:
            explanation = "Poor blueprint - insufficient structure or clarity"
        
        return score, explanation
    
    def _get_metric_synonyms(self, aggregation: str) -> List[str]:
        """Get synonyms for SQL aggregation functions."""
        synonyms = {
            'count': ['total', 'number', 'quantity'],
            'sum': ['total', 'aggregate'],
            'avg': ['average', 'mean'],
            'min': ['minimum', 'lowest'],
            'max': ['maximum', 'highest', 'peak'],
            'distinct': ['unique', 'different']
        }
        return synonyms.get(aggregation, [])
    
    def _extract_where_clause(self, sql_query: str) -> str:
        """Extract WHERE clause from SQL query."""
        sql_lower = sql_query.lower()
        where_start = sql_lower.find('where')
        if where_start == -1:
            return ""
        
        # Find the end of WHERE clause (before GROUP BY, ORDER BY, HAVING, etc.)
        end_keywords = ['group by', 'order by', 'having', 'limit', 'union', ';']
        where_end = len(sql_query)
        
        for keyword in end_keywords:
            pos = sql_lower.find(keyword, where_start)
            if pos != -1:
                where_end = min(where_end, pos)
        
        return sql_query[where_start:where_end].strip()
    
    def _assess_filter_alignment(self, where_clause: str, key_filters: str) -> float:
        """Assess alignment between WHERE clause and described filters."""
        if not where_clause or not key_filters:
            return 0.0
        
        where_lower = where_clause.lower()
        filters_lower = key_filters.lower()
        
        # Extract potential filter terms from WHERE clause
        filter_indicators = ['=', '!=', '<>', '>', '<', '>=', '<=', 'like', 'in', 'between', 'is null', 'is not null']
        date_indicators = ['date', 'timestamp', 'year', 'month', 'day']
        
        alignment_score = 0.0
        max_score = 0.0
        
        # Check for common filter patterns
        if any(indicator in where_lower for indicator in filter_indicators):
            max_score += 1
            if any(term in filters_lower for term in ['filter', 'where', 'condition']):
                alignment_score += 0.5
        
        # Check for date filters
        if any(indicator in where_lower for indicator in date_indicators):
            max_score += 1
            if any(term in filters_lower for term in ['date', 'time', 'period', 'year', 'month']):
                alignment_score += 1
        
        return alignment_score / max_score if max_score > 0 else 0.0
    
    def _assess_sql_complexity(self, sql_query: str) -> int:
        """Assess SQL query complexity on a scale of 1-5."""
        sql_lower = sql_query.lower()
        complexity = 1
        
        # Check for various SQL features
        if 'join' in sql_lower:
            complexity += 1
        if any(func in sql_lower for func in ['count(', 'sum(', 'avg(', 'min(', 'max(']):
            complexity += 1
        if 'group by' in sql_lower:
            complexity += 1
        if any(clause in sql_lower for clause in ['having', 'union', 'subquery', 'case when']):
            complexity += 1
        
        return min(5, complexity)
    
    def perform_assessment(self) -> None:
        """Perform quality assessment on all rows."""
        print("\n🔍 Starting Quality Assessment...")
        
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        # Initialize new columns
        semantic_scores = []
        deconstruction_scores = []
        blueprint_scores = []
        rationales = []
        
        # Process each row
        for idx, row in self.df.iterrows():
            if idx % 100 == 0:
                print(f"   Processing row {idx + 1}/{len(self.df)}...")
            
            # Assess each criterion
            semantic_score, semantic_reason = self.assess_semantic_clarity(row)
            deconstruction_score, deconstruction_reason = self.assess_deconstruction_accuracy(row)
            blueprint_score, blueprint_reason = self.assess_blueprint_potential(row)
            
            # Combine rationale
            rationale = f"Semantic: {semantic_reason}. Deconstruction: {deconstruction_reason}. Blueprint: {blueprint_reason}."
            
            # Store results
            semantic_scores.append(semantic_score)
            deconstruction_scores.append(deconstruction_score)
            blueprint_scores.append(blueprint_score)
            rationales.append(rationale)
        
        # Add new columns to DataFrame
        self.df['Semantic_Clarity_Score'] = semantic_scores
        self.df['Deconstruction_Accuracy_Score'] = deconstruction_scores
        self.df['Blueprint_Potential_Score'] = blueprint_scores
        self.df['Rationale'] = rationales
        
        # Calculate overall average score
        self.df['Average_Score'] = (
            self.df['Semantic_Clarity_Score'] + 
            self.df['Deconstruction_Accuracy_Score'] + 
            self.df['Blueprint_Potential_Score']
        ) / 3
        
        print("✅ Quality assessment completed!")
    
    def save_results(self, output_file: str = "Final_Results_With_Quality_Scores.xlsx") -> None:
        """Save the results with quality scores to Excel file."""
        if self.df is None:
            raise ValueError("No assessment results to save.")
        
        print(f"\n💾 Saving results to: {output_file}")
        
        try:
            # Save to Excel
            self.df.to_excel(output_file, index=False, engine='openpyxl')
            print(f"✅ Results saved successfully to {output_file}")
            
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
            raise
    
    def generate_executive_summary(self) -> Dict:
        """Generate executive summary of quality assessment results."""
        if self.df is None:
            raise ValueError("No assessment results available.")
        
        print("\n📊 Generating Executive Summary...")
        
        # Calculate average scores
        avg_semantic = self.df['Semantic_Clarity_Score'].mean()
        avg_deconstruction = self.df['Deconstruction_Accuracy_Score'].mean()
        avg_blueprint = self.df['Blueprint_Potential_Score'].mean()
        avg_overall = self.df['Average_Score'].mean()
        
        # Calculate AI-Ready percentage (average score >= 4.0)
        ai_ready_count = (self.df['Average_Score'] >= 4.0).sum()
        ai_ready_percentage = (ai_ready_count / len(self.df)) * 100
        
        # Additional statistics
        total_reports = len(self.df)
        high_quality_reports = (self.df['Average_Score'] >= 4.0).sum()
        medium_quality_reports = ((self.df['Average_Score'] >= 3.0) & (self.df['Average_Score'] < 4.0)).sum()
        low_quality_reports = (self.df['Average_Score'] < 3.0).sum()
        
        # Distribution by score ranges
        score_distribution = {
            'Excellent (4.5-5.0)': ((self.df['Average_Score'] >= 4.5).sum() / total_reports * 100),
            'Good (4.0-4.5)': (((self.df['Average_Score'] >= 4.0) & (self.df['Average_Score'] < 4.5)).sum() / total_reports * 100),
            'Fair (3.0-4.0)': (((self.df['Average_Score'] >= 3.0) & (self.df['Average_Score'] < 4.0)).sum() / total_reports * 100),
            'Poor (2.0-3.0)': (((self.df['Average_Score'] >= 2.0) & (self.df['Average_Score'] < 3.0)).sum() / total_reports * 100),
            'Very Poor (<2.0)': ((self.df['Average_Score'] < 2.0).sum() / total_reports * 100)
        }
        
        summary = {
            'total_reports': total_reports,
            'average_scores': {
                'semantic_clarity': round(avg_semantic, 2),
                'deconstruction_accuracy': round(avg_deconstruction, 2),
                'blueprint_potential': round(avg_blueprint, 2),
                'overall_average': round(avg_overall, 2)
            },
            'ai_ready': {
                'count': high_quality_reports,
                'percentage': round(ai_ready_percentage, 1)
            },
            'quality_distribution': {
                'high_quality': high_quality_reports,
                'medium_quality': medium_quality_reports,
                'low_quality': low_quality_reports
            },
            'score_distribution': {k: round(v, 1) for k, v in score_distribution.items()}
        }
        
        return summary
    
    def print_executive_summary(self, summary: Dict) -> None:
        """Print formatted executive summary."""
        print("\n" + "="*80)
        print("🎯 EXECUTIVE SUMMARY - BUSINESS CONTEXT QUALITY ASSESSMENT")
        print("="*80)
        
        print(f"\n📊 OVERALL STATISTICS")
        print(f"   Total Reports Analyzed: {summary['total_reports']:,}")
        
        print(f"\n📈 AVERAGE QUALITY SCORES (1-5 scale)")
        scores = summary['average_scores']
        print(f"   Semantic Clarity Score:      {scores['semantic_clarity']}")
        print(f"   Deconstruction Accuracy:     {scores['deconstruction_accuracy']}")
        print(f"   Blueprint Potential Score:   {scores['blueprint_potential']}")
        print(f"   Overall Average Score:       {scores['overall_average']}")
        
        print(f"\n🤖 AI-READINESS ASSESSMENT")
        ai_ready = summary['ai_ready']
        print(f"   Reports with Average Score ≥ 4.0: {ai_ready['count']:,} ({ai_ready['percentage']}%)")
        
        status = "✅ READY" if ai_ready['percentage'] >= 70 else "⚠️ NEEDS IMPROVEMENT" if ai_ready['percentage'] >= 50 else "❌ NOT READY"
        print(f"   AI Integration Status:         {status}")
        
        print(f"\n📈 QUALITY DISTRIBUTION")
        dist = summary['quality_distribution']
        print(f"   High Quality (≥4.0):    {dist['high_quality']:,} reports")
        print(f"   Medium Quality (3.0-4.0): {dist['medium_quality']:,} reports")
        print(f"   Low Quality (<3.0):      {dist['low_quality']:,} reports")
        
        print(f"\n📊 DETAILED SCORE BREAKDOWN")
        for category, percentage in summary['score_distribution'].items():
            print(f"   {category}: {percentage}%")
        
        print(f"\n🎯 CONCLUSION")
        if ai_ready['percentage'] >= 70:
            conclusion = "Dataset is READY for AI integration. High-quality business context generation achieved."
        elif ai_ready['percentage'] >= 50:
            conclusion = "Dataset shows GOOD POTENTIAL but requires targeted improvements in lower-scoring entries."
        else:
            conclusion = "Dataset REQUIRES SIGNIFICANT IMPROVEMENT before AI integration. Consider reprocessing."
        
        print(f"   {conclusion}")
        
        print("\n" + "="*80)


def main():
    """Main execution function."""
    input_file = "FINAL_METABASE_REPORTS_WITH_BUSINESS_CONTEXT_20250801.xlsx"
    
    try:
        # Initialize assessor
        assessor = BusinessContextQualityAssessor(input_file)
        
        # Load and analyze data
        assessor.load_data()
        assessor.perform_assessment()
        
        # Save results
        assessor.save_results()
        
        # Generate and display executive summary
        summary = assessor.generate_executive_summary()
        assessor.print_executive_summary(summary)
        
        print("\n✨ Quality assessment completed successfully!")
        
    except Exception as e:
        print(f"💥 Assessment failed: {str(e)}")
        raise


if __name__ == "__main__":
    main() 