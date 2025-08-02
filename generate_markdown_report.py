#!/usr/bin/env python3
"""
Generate comprehensive markdown report from AI summary assessment results.
"""

import pandas as pd
import numpy as np
from datetime import datetime

def generate_markdown_report():
    """Generate a comprehensive markdown report from assessment results."""
    
    try:
        # Load the assessment results
        df = pd.read_excel('ai_summary_assessment_results.xlsx')
        print(f"📊 Loaded {len(df):,} assessment results")
        
        # Calculate key metrics
        total_reports = len(df)
        
        # Overall quality distribution
        quality_counts = df['Overall_Assessment'].value_counts()
        good_count = quality_counts.get('Good', 0)
        avg_count = quality_counts.get('Average', 0)
        poor_count = quality_counts.get('Poor', 0)
        
        good_pct = (good_count / total_reports) * 100
        avg_pct = (avg_count / total_reports) * 100
        poor_pct = (poor_count / total_reports) * 100
        
        # Score distributions
        spec_dist = df['Specificity_Score'].value_counts().sort_index()
        intent_dist = df['Intent_Score'].value_counts().sort_index()
        
        # Key levers
        levers_counts = df['Key_Levers_Identified'].value_counts()
        levers_yes = levers_counts.get('Yes', 0)
        levers_partial = levers_counts.get('Partial', 0)
        levers_no = levers_counts.get('No', 0)
        
        # Average scores
        avg_spec = df['Specificity_Score'].mean()
        avg_intent = df['Intent_Score'].mean()
        
        # Poor assessment analysis
        poor_df = df[df['Overall_Assessment'] == 'Poor']
        poor_low_spec_count = len(poor_df[poor_df['Specificity_Score'] <= 2])
        poor_no_levers_count = len(poor_df[poor_df['Key_Levers_Identified'] == 'No'])
        
        # SQL analysis
        avg_filters = df['SQL_Filters_Found'].mean()
        no_filters_count = len(df[df['SQL_Filters_Found'] == 0])
        complex_queries_count = len(df[df['SQL_Filters_Found'] > 5])
        
        # Get examples
        good_examples = df[df['Overall_Assessment'] == 'Good']['Report Name'].head(3).tolist()
        avg_examples = df[df['Overall_Assessment'] == 'Average']['Report Name'].head(3).tolist()
        poor_examples = df[df['Overall_Assessment'] == 'Poor']['Report Name'].head(3).tolist()
        
        # Generate the markdown report
        report = f"""# AI Summary Quality Assessment Report

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Executive Summary

This report analyzes the quality of AI-generated summaries for **{total_reports:,} Metabase reports** by evaluating their specificity, business intent, and ability to identify key business levers from SQL queries.

### 🎯 Key Findings

- **Overall Quality**: {good_pct:.1f}% Good, {avg_pct:.1f}% Average, {poor_pct:.1f}% Poor
- **Average Specificity Score**: {avg_spec:.2f}/5.00
- **Average Intent Score**: {avg_intent:.2f}/5.00
- **Key Business Levers Identified**: {(levers_yes/total_reports)*100:.1f}% Yes, {(levers_partial/total_reports)*100:.1f}% Partial, {(levers_no/total_reports)*100:.1f}% No

---

## 📊 Detailed Analysis

### 1. Overall Quality Distribution

| Assessment | Count | Percentage | Quality Level |
|------------|-------|------------|---------------|
| 🟢 Good       | {good_count:,} | {good_pct:.1f}% | High-quality summaries |
| 🟡 Average    | {avg_count:,} | {avg_pct:.1f}% | Partially useful summaries |
| 🔴 Poor       | {poor_count:,} | {poor_pct:.1f}% | Inadequate summaries |
| **Total**     | **{total_reports:,}** | **100.0%** | |

### 2. Score Distribution Analysis

#### Specificity Scores (How specific are the summaries?)

| Score | Count | Percentage | Description |
|-------|-------|------------|-------------|
| 5 ⭐⭐⭐⭐⭐ | {spec_dist.get(5, 0):,} | {(spec_dist.get(5, 0)/total_reports)*100:.1f}% | Highly Specific - mentions specific entities |
| 4 ⭐⭐⭐⭐ | {spec_dist.get(4, 0):,} | {(spec_dist.get(4, 0)/total_reports)*100:.1f}% | Quite Specific - good entity identification |
| 3 ⭐⭐⭐ | {spec_dist.get(3, 0):,} | {(spec_dist.get(3, 0)/total_reports)*100:.1f}% | Somewhat Specific - broader categories |
| 2 ⭐⭐ | {spec_dist.get(2, 0):,} | {(spec_dist.get(2, 0)/total_reports)*100:.1f}% | Low Specificity - generic terms |
| 1 ⭐ | {spec_dist.get(1, 0):,} | {(spec_dist.get(1, 0)/total_reports)*100:.1f}% | Very Generic - high-level descriptions |

#### Intent Scores (Business vs Technical focus)

| Score | Count | Percentage | Description |
|-------|-------|------------|-------------|
| 5 🎯🎯🎯🎯🎯 | {intent_dist.get(5, 0):,} | {(intent_dist.get(5, 0)/total_reports)*100:.1f}% | Strong Business Intent |
| 4 🎯🎯🎯🎯 | {intent_dist.get(4, 0):,} | {(intent_dist.get(4, 0)/total_reports)*100:.1f}% | Good Business Intent |
| 3 🎯🎯🎯 | {intent_dist.get(3, 0):,} | {(intent_dist.get(3, 0)/total_reports)*100:.1f}% | Mixed Intent |
| 2 🎯🎯 | {intent_dist.get(2, 0):,} | {(intent_dist.get(2, 0)/total_reports)*100:.1f}% | Mostly Technical |
| 1 🎯 | {intent_dist.get(1, 0):,} | {(intent_dist.get(1, 0)/total_reports)*100:.1f}% | Technical Only |

### 3. Key Business Levers Analysis

| Identification Level | Count | Percentage | Impact |
|---------------------|-------|------------|---------|
| ✅ Yes - Identifies most key filters | {levers_yes:,} | {(levers_yes/total_reports)*100:.1f}% | High business value |
| ⚠️ Partial - Identifies some filters | {levers_partial:,} | {(levers_partial/total_reports)*100:.1f}% | Medium business value |
| ❌ No - Misses key business filters | {levers_no:,} | {(levers_no/total_reports)*100:.1f}% | Low business value |

---

## 🔍 Problem Analysis

### Primary Issues Identified

1. **🚨 Low Specificity Crisis**: {((spec_dist.get(1, 0) + spec_dist.get(2, 0))/total_reports)*100:.1f}% of summaries (scores ≤2) lack specific business context
2. **🔍 Filter Detection Gap**: {(levers_no/total_reports)*100:.1f}% fail to identify key business levers from SQL
3. **📝 Generic Language Overuse**: {(spec_dist.get(1, 0)/total_reports)*100:.1f}% use only high-level, generic descriptions

### Failure Pattern Analysis

Among the **{poor_count:,} "Poor" assessments**:
- **{(poor_low_spec_count/max(poor_count, 1))*100:.1f}%** have critically low specificity (≤2)
- **{(poor_no_levers_count/max(poor_count, 1))*100:.1f}%** completely miss key business filters
- **Average specificity** in poor assessments: {poor_df['Specificity_Score'].mean() if len(poor_df) > 0 else 0:.2f}

### SQL Complexity Insights

- **Average filters per query**: {avg_filters:.1f}
- **Queries with no identifiable filters**: {no_filters_count:,} ({(no_filters_count/total_reports)*100:.1f}%)
- **Complex queries** (>5 filters): {complex_queries_count:,} ({(complex_queries_count/total_reports)*100:.1f}%)

---

## 📋 Examples by Quality Category

### 🟢 Good Quality Examples
*Reports scoring 4-5 on both specificity and intent*

{chr(10).join([f"- {name}" for name in good_examples])}

### 🟡 Average Quality Examples  
*Reports with mixed scores - partially useful*

{chr(10).join([f"- {name}" for name in avg_examples])}

### 🔴 Poor Quality Examples
*Reports with low specificity or missing key business context*

{chr(10).join([f"- {name}" for name in poor_examples])}

---

## 💡 Strategic Recommendations

### 🎯 Immediate Actions Required

1. **Improve Specificity Training**
   - **Current**: {avg_spec:.2f}/5.00 average specificity
   - **Target**: >4.0/5.00
   - **Action**: Train AI to extract specific entity names from report titles
   - **Focus**: Business-specific terminology rather than generic descriptions

2. **Enhance Filter Detection**
   - **Current**: {(levers_no/total_reports)*100:.1f}% miss key business levers
   - **Target**: <20% missing key levers
   - **Action**: Implement better SQL WHERE clause analysis
   - **Focus**: Business-critical filters (status, type, category)

3. **Maintain Business Focus** ✅
   - **Current**: {avg_intent:.2f}/5.00 (Strong performance)
   - **Action**: Continue emphasizing business context over technical implementation

### 🚀 Long-term Improvements

1. **Quality Threshold Implementation**
   - Set minimum specificity score of 3 for production summaries
   - Flag reports with "No" key lever identification for review

2. **Training Data Enhancement**
   - Use {good_count:,} "Good" quality examples as training templates
   - Focus training on the {poor_count:,} poor-quality patterns identified

3. **Automated Quality Gates**
   - Implement real-time assessment before summary publication
   - Alert when specificity drops below threshold

---

## 📊 Statistical Summary

| Metric | Value | Status |
|--------|-------|--------|
| Total Reports Analyzed | {total_reports:,} | ✅ Complete |
| Average Specificity Score | {avg_spec:.2f}/5.00 | ⚠️ Needs Improvement |
| Average Intent Score | {avg_intent:.2f}/5.00 | ✅ Good |
| High Quality Rate (Good) | {good_pct:.1f}% | ⚠️ Low |
| Acceptable Quality Rate (Good + Average) | {(good_pct + avg_pct):.1f}% | ⚠️ Moderate |
| Critical Issues (Poor) | {poor_pct:.1f}% | ⚠️ High |
| Business Lever Detection Success | {((levers_yes + levers_partial)/total_reports)*100:.1f}% | ⚠️ Needs Improvement |
| SQL Queries with Complex Filters | {(complex_queries_count/total_reports)*100:.1f}% | ℹ️ Reference |

---

## 🎯 Success Metrics & Targets

### Current State vs Targets

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Good Quality Summaries | {good_pct:.1f}% | 25%+ | {25 - good_pct:+.1f}% |
| Average Specificity | {avg_spec:.2f} | 4.0+ | {4.0 - avg_spec:+.2f} |
| Key Lever Detection (Yes) | {(levers_yes/total_reports)*100:.1f}% | 60%+ | {60 - (levers_yes/total_reports)*100:+.1f}% |
| Poor Quality Rate | {poor_pct:.1f}% | <15% | {poor_pct - 15:+.1f}% |

---

## 🔄 Next Steps

### Week 1: Quick Wins
- [ ] Analyze top 10 "Good" examples to identify success patterns
- [ ] Create specificity training dataset from high-scoring reports
- [ ] Implement basic filter detection improvements

### Month 1: Core Improvements  
- [ ] Deploy enhanced specificity scoring model
- [ ] Improve SQL filter extraction algorithms
- [ ] Set up automated quality monitoring

### Quarter 1: Systematic Enhancement
- [ ] Achieve 15%+ Good quality rate (vs current {good_pct:.1f}%)
- [ ] Reduce Poor quality rate to <20% (vs current {poor_pct:.1f}%)
- [ ] Improve key lever detection to 50%+ Yes rate

---

## 🏁 Conclusion

The analysis reveals **significant opportunities for improvement** in AI summary quality. While the AI demonstrates **good business intent** ({avg_intent:.2f}/5.00 average), **specificity remains a critical weakness** ({avg_spec:.2f}/5.00 average).

### 🚨 Most Urgent Issue
**{(levers_no/total_reports)*100:.1f}% of summaries fail to identify key business levers** - this directly impacts business users' ability to understand what the queries actually measure.

### 🎯 Success Path
With focused improvements in specificity and filter detection, the overall quality distribution could shift from **{good_pct:.1f}% Good** to a target of **25%+ Good quality summaries**.

### 💪 Leverage Existing Strengths
The strong business intent scores ({(intent_dist.get(4,0) + intent_dist.get(5,0))/total_reports*100:.1f}% scoring 4-5) provide a solid foundation for building enhanced specificity and technical accuracy.

---

*Report generated by AI Summary Quality Assessment Tool*  
*Data source: `metabase_reports_analysis.xlsx`*  
*Assessment results: `ai_summary_assessment_results.xlsx`*
"""
        
        # Write the report
        with open('AI_Summary_Quality_Assessment_Report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("✅ Comprehensive markdown report generated!")
        print("📄 File: AI_Summary_Quality_Assessment_Report.md")
        print(f"📊 Report covers {total_reports:,} assessments with detailed analysis")
        
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_markdown_report() 