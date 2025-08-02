# Gemini Business Context Generator

A comprehensive Python solution for generating structured business context summaries from Metabase reports using Google's Gemini 2.5 Pro model.

## 🎯 Overview

This project processes Metabase reports stored in Excel format and generates "smarter," structured business context for each report using advanced AI. The system uses **Gemini 2.5 Pro** (Google's flagship reasoning model) to analyze SQL queries and create business-friendly summaries.

### Key Features

- ✅ **Secure API Key Management** - Environment variable-based security
- ✅ **Rate Limiting** - Respects 60 RPM API limits with 1.5s delays
- ✅ **Robust Error Handling** - Continues processing even if individual reports fail
- ✅ **Structured Output** - Consistent markdown format for business context
- ✅ **Comprehensive Logging** - Detailed logs for monitoring and debugging
- ✅ **Excel Integration** - Reads input and saves results in Excel format

## 📋 Requirements

### System Requirements
- Python 3.8+
- pip package manager
- Internet connection for Gemini API calls

### API Requirements
- Google Gemini API key (free tier available)
- Google AI Studio account

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pandas` - Data manipulation
- `openpyxl` - Excel file handling  
- `google-generativeai` - Gemini API client
- Other supporting libraries

### 2. Set Up Gemini API Key

**Option A: Use the Helper Script (Recommended)**
```bash
python3 setup_gemini_api_key.py
```

**Option B: Manual Setup**
```bash
# Get your API key from: https://aistudio.google.com/app/apikey
export GEMINI_API_KEY='your-api-key-here'
```

### 3. Verify Your Data

```bash
python3 examine_excel_structure.py
```

This verifies your Excel file has the required columns:
- `report_name`
- `description` 
- `sql_query`

### 4. Process Reports

```bash
python3 gemini_business_context_generator.py
```

## 📊 Input Data Format

The script expects an Excel file (`metabase_reports_detailed_20250731_122354.xlsx`) with these columns:

| Column | Description | Required |
|--------|-------------|----------|
| `report_name` | Name of the Metabase report | ✅ Yes |
| `description` | Report description | Optional |
| `sql_query` | SQL query for the report | ✅ Yes |
| Other columns | Metadata (preserved in output) | No |

### Sample Data
```
report_name: "Monthly Revenue by Region"
description: "Shows revenue breakdown by geographic region"
sql_query: "SELECT region, SUM(revenue) FROM sales WHERE date >= '2024-01-01' GROUP BY region"
```

## 🎯 Output Format

The Gemini model generates structured business context in this exact format:

```markdown
---
**Business Question:** What is the monthly revenue performance across different geographic regions?
**Primary Metric(s):**
- Total Revenue (SUM of revenue)
- Geographic Distribution
**Key Filters / Levers:**
- Date Range (from 2024-01-01)
- Geographic Region
**Final Summary:** This report analyzes revenue performance by geographic region to identify top-performing markets and regional trends.
---
```

## 📁 Output Files

The script generates an Excel file with multiple sheets:

### 1. Business_Context_Results
Contains the main results with these columns:
- `report_id` - Unique identifier
- `original_report_name` - Original report name
- `original_description` - Original description
- `original_sql_query` - Original SQL query
- `business_question` - Generated business question
- `primary_metrics` - Identified key metrics
- `key_filters` - Business filters/levers
- `final_summary` - Concise business summary
- `raw_response` - Full Gemini response
- `processing_timestamp` - When processed

### 2. Processing_Summary
Overview statistics:
- Total reports processed
- Success/failure counts
- Success rate percentage
- Processing date and model used

### 3. Failed_Reports (if any)
Details of reports that failed to process:
- Report ID and name
- Error description
- Troubleshooting information

## ⚙️ Configuration

### Model Settings
- **Model**: `gemini-2.5-pro` (recommended for quality)
- **Temperature**: 0.1 (consistent, structured output)
- **Max Output Tokens**: 2048
- **Rate Limiting**: 1.5 seconds between requests

### Alternative Models
For cost optimization, you can modify the code to use:
- `gemini-2.5-flash` (14x cheaper, good quality)
- `gemini-2.0-flash` (21x cheaper, basic quality)

## 🔧 Troubleshooting

### Common Issues

**1. API Key Problems**
```
❌ Gemini API key not found in environment variables
```
- Solution: Run `python3 setup_gemini_api_key.py`
- Or manually set: `export GEMINI_API_KEY='your-key'`

**2. Column Name Mismatch**
```
❌ Missing required columns: ['report_name']
```
- Solution: Check column names with `python3 examine_excel_structure.py`
- Update script if column names differ

**3. Rate Limiting**
```
⚠️ API call failed - quota exceeded
```
- Solution: The script automatically handles rate limiting
- Check your API quota at Google AI Studio

**4. Content Filtering**
```
⚠️ Content blocked by safety filters
```
- Solution: This is automatic for certain SQL content
- Review the Failed_Reports sheet for details

### Logs and Debugging

The script creates detailed logs in `gemini_business_context.log`:
```bash
tail -f gemini_business_context.log
```

## 💰 Cost Estimation

Based on Gemini 2.5 Pro pricing (as of January 2025):

| Reports | Input Cost | Output Cost | Total Cost |
|---------|------------|-------------|------------|
| 100 | $0.25 | $1.00 | **$1.25** |
| 1,000 | $2.50 | $10.00 | **$12.50** |
| 1,555 | $3.89 | $15.55 | **$19.44** |

*Assumes ~2,000 input tokens and ~1,000 output tokens per report*

## 🔄 Processing Workflow

1. **Load Data** - Read Excel file and validate structure
2. **Setup API** - Configure Gemini 2.5 Pro with security settings
3. **Process Reports** - For each report:
   - Create structured prompt
   - Call Gemini API
   - Parse structured response
   - Handle errors gracefully
   - Apply rate limiting
4. **Save Results** - Export to multi-sheet Excel file
5. **Generate Summary** - Display processing statistics

## 📈 Performance Metrics

For 1,555 reports (actual dataset):
- **Estimated Processing Time**: ~45 minutes (with 1.5s delays)
- **Expected Success Rate**: 95%+ 
- **Memory Usage**: ~50MB
- **Log File Size**: ~5MB

## 🛡️ Security Best Practices

1. **Never hardcode API keys** in source code
2. **Use environment variables** for sensitive data
3. **Rotate API keys** regularly
4. **Monitor API usage** and costs
5. **Keep logs secure** (may contain business data)

## 🔮 Future Enhancements

### Potential Improvements
1. **Hybrid Model Routing** - Use different models based on query complexity
2. **Batch Processing** - Process multiple reports in single API calls
3. **Quality Scoring** - Rate the quality of generated context
4. **Custom Templates** - Industry-specific prompt templates
5. **Real-time Processing** - Direct integration with Metabase API

### Alternative Approaches
1. **Cost Optimization**: Switch to Gemini 2.5 Flash for 14x cost reduction
2. **Speed Optimization**: Parallel processing with multiple API keys
3. **Quality Enhancement**: Two-pass processing with validation

## 📞 Support

For issues or questions:
1. Check this README
2. Review log files (`gemini_business_context.log`)
3. Run diagnostic scripts (`examine_excel_structure.py`)
4. Verify API setup (`setup_gemini_api_key.py`)

## 📄 License

This project is developed for internal business intelligence use. Ensure compliance with:
- Google AI Terms of Service
- Your organization's data policies
- Applicable privacy regulations

---

**Created by**: Business Intelligence Team  
**Date**: January 2025  
**Model**: Gemini 2.5 Pro (recommended)  
**Status**: Ready for Production Use 