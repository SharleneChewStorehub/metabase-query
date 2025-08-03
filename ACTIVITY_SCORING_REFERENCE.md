# Activity Scoring System - Reference Guide

**Version:** 1.0  
**Last Updated:** August 3, 2025  
**Applies To:** All Metabase report usage analytics

---

## 🎯 **Overview**

Our activity scoring system provides a comprehensive, data-driven approach to prioritizing Metabase reports based on actual usage patterns over the past 12 months. This scoring mechanism helps identify which reports deliver real business value and should be prioritized for AI enhancement, maintenance, or potential archiving.

---

## 📊 **Scoring Components**

### **1. Recent Query Activity (10 points maximum)**
- **Criteria:** Report has been executed within the past 12 months
- **Score:** 10 points if `last_query_start` is within 12 months, 0 points otherwise
- **Rationale:** Direct usage is the strongest indicator of business value
- **Data Source:** `last_query_start` field from Metabase API

### **2. Dashboard Usage (1-5 points maximum)**
- **Criteria:** Number of dashboards that embed or reference this report
- **Scoring Scale:** 
  - 1 dashboard = 1 point
  - 2 dashboards = 2 points
  - 3 dashboards = 3 points
  - 4 dashboards = 4 points
  - 5+ dashboards = 5 points (capped at 5)
- **Rationale:** Dashboard integration indicates report is actively viewed by end users
- **Data Source:** `dashboard_count` field from Metabase API

### **3. Parameter Usage (1-3 points maximum)**
- **Criteria:** Frequency of interactive parameter usage in the report
- **Scoring Scale:**
  - Low usage = 1 point
  - Medium usage = 2 points
  - High usage = 3 points (capped at 3)
- **Rationale:** Parameter interaction shows reports are being actively explored and customized
- **Data Source:** `parameter_usage_count` field from Metabase API

---

## 🏆 **Score Categories**

### **🔥 High Activity (11+ points)**
- **Definition:** Reports with both recent query activity (10 pts) AND significant dashboard/parameter usage (1+ pts)
- **Count:** 406 reports (26.2% of analyzed reports)
- **Business Impact:** Premium candidates for AI enhancement
- **Recommended Action:** Immediate priority for NL-to-SQL development

### **📊 Medium Activity (6-10 points)**
- **Definition:** Reports with either recent activity OR substantial dashboard integration
- **Count:** 331 reports (21.4% of analyzed reports)
- **Business Impact:** Moderate value with specific use cases
- **Recommended Action:** Secondary priority for AI enhancement

### **📉 Low Activity (1-5 points)**
- **Definition:** Reports with minimal usage - typically dashboard-only or parameter-only usage
- **Count:** 234 reports (15.1% of analyzed reports)
- **Business Impact:** Limited current value but may have potential
- **Recommended Action:** Evaluate for improvement or archive

### **❌ No Activity (0 points)**
- **Definition:** Reports with no recorded usage in the past 12 months
- **Count:** 579 reports (37.4% of analyzed reports)
- **Business Impact:** Strong candidates for archiving
- **Recommended Action:** Archive or sunset unless strategic value identified

---

## 📈 **Usage Status Classification**

### **Recently Used (968 reports - 62.5%)**
- **Criteria:** `is_recently_used = True`
- **Definition:** Report executed at least once in past 12 months OR embedded in active dashboards
- **Business Value:** Confirmed active business usage
- **Priority:** Maintain and enhance

### **Unused (582 reports - 37.5%)**
- **Criteria:** `is_recently_used = False`
- **Definition:** No query activity in past 12 months AND no dashboard integration
- **Business Value:** Questionable current relevance
- **Priority:** Review for archiving

---

## 🔧 **Technical Implementation**

### **Data Collection Process**
1. **API Extraction:** Fetch usage data via Metabase `/api/card/{id}` endpoint
2. **Timestamp Analysis:** Parse `last_query_start` against 12-month threshold
3. **Dashboard Integration:** Count active dashboard references
4. **Parameter Analysis:** Assess interactive usage patterns
5. **Score Calculation:** Apply weighted scoring algorithm
6. **Classification:** Assign activity categories and usage status

### **Calculation Algorithm**
```python
def calculate_activity_score(detailed_card: dict) -> tuple:
    activity_score = 0
    is_recently_used = False
    
    # Recent Query Activity (10 points)
    if last_query_start and query_time >= twelve_months_ago:
        is_recently_used = True
        activity_score += 10
    
    # Dashboard Usage (1-5 points)
    if dashboard_count > 0:
        activity_score += min(dashboard_count, 5)
        is_recently_used = True
    
    # Parameter Usage (1-3 points)
    if parameter_usage_count > 0:
        activity_score += min(parameter_usage_count, 3)
    
    return activity_score, is_recently_used
```

### **Data Refresh Frequency**
- **Recommended:** Monthly analysis for trending insights
- **Minimum:** Quarterly analysis for strategic planning
- **Real-time:** Available via Metabase API for on-demand analysis

---

## 📋 **Business Applications**

### **AI Development Prioritization**
1. **Phase 1:** Focus on 406 high-activity reports (11+ score)
2. **Phase 2:** Enhance 331 medium-activity reports (6-10 score)
3. **Phase 3:** Evaluate 234 low-activity reports for potential

### **Resource Allocation**
- **Development Resources:** Prioritize high-activity reports
- **Maintenance Resources:** Focus on recently used reports
- **Archive Resources:** Process unused reports for storage optimization

### **Strategic Planning**
- **Growth Opportunities:** Identify reports with dashboard integration but low query activity
- **Deprecation Candidates:** Target reports with 0 activity score for sunset
- **Enhancement Targets:** Focus on high-score reports for advanced features

---

## 🎯 **Quality Indicators**

### **High-Value Report Characteristics**
- Activity score 11+ (recent usage + integration)
- Multiple dashboard embeddings (3+ dashboards)
- Regular query patterns (consistent `last_query_start` updates)
- Parameter interaction (evidence of exploration)

### **Archive Candidate Characteristics**
- Activity score 0 (no recent usage)
- No dashboard integration
- Stale `last_query_start` (>12 months old)
- No parameter usage

### **Enhancement Opportunities**
- High dashboard count but low query activity (potential user experience issues)
- Recent queries but no dashboard integration (potential for broader adoption)
- Parameter usage without dashboard integration (candidates for embedded analytics)

---

## 📊 **Reporting & Monitoring**

### **Key Performance Indicators (KPIs)**
- **Active Report Percentage:** Target >65% recently used
- **High-Value Report Ratio:** Target >25% with 11+ activity score
- **Dashboard Integration Rate:** Target >40% of active reports
- **Archive Efficiency:** Target <30% zero-activity reports

### **Monthly Report Metrics**
- Total reports analyzed
- Activity score distribution
- Usage trend analysis (month-over-month)
- Dashboard integration changes
- Archive candidates identified

### **Executive Dashboard Components**
- Activity score heat map
- Usage trend visualization
- ROI analysis by report category
- Resource allocation recommendations

---

**For technical implementation details, see:** `add_usage_to_final_reports.py`  
**For validation procedures, see:** `test_usage_enrichment.py`  
**For complete usage data, see:** `FINAL_METABASE_REPORTS_WITH_USAGE_CONTEXT_*.xlsx` 