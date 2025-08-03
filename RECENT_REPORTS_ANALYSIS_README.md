# Recent Reports Analysis Tool

## 🚨 **CRITICAL SAFETY PROTOCOL**
This tool operates under **STRICT READ-ONLY** protocols:
- **ONLY** uses GET requests for data retrieval
- **NO** modifications, deletions, or updates to Metabase instance
- Designed exclusively for analysis and reporting purposes

## Overview

The Recent Reports Fetcher is a Python script designed to identify and analyze Metabase reports that have been viewed in the last 12 months but haven't been previously processed. This tool is perfect for ongoing analysis projects where you want to focus on newly active reports.

## Key Features

### 🎯 **Smart Report Discovery**
- Identifies reports viewed within the last 12 months using Metabase view logs
- Automatically excludes previously analyzed reports
- Counts view frequency for prioritization

### 🔍 **Comprehensive Data Collection**
- Fetches full report details including SQL queries
- Translates collection IDs to human-readable collection names
- Filters for native SQL queries only (skips GUI-built queries)

### 🛡️ **Built-in Safety & Error Handling**
- Enforces read-only operations with multiple safety checks
- Graceful handling of missing or inaccessible reports
- Polite API rate limiting (500ms delays between calls)
- Comprehensive logging for debugging

### 📊 **Rich Output Format**
- Clean pandas DataFrame with all essential columns
- View count tracking for the last 12 months
- Timestamped Excel output files

## Installation

### Prerequisites
Ensure you have the required dependencies installed:

```bash
pip install pandas requests openpyxl python-dotenv
```

### Files Required
- `metabase_reports_detailed_20250731_122354.xlsx` - Previous analysis results for exclusion
- `recent_reports_fetcher.py` - The main script

## Usage

### Basic Usage

1. **Run the script:**
   ```bash
   python3 recent_reports_fetcher.py
   ```

2. **Provide credentials when prompted:**
   - Metabase URL (e.g., `https://your-metabase.com`)
   - API Key (entered securely, not displayed)

3. **Wait for processing:**
   - The script will show progress as it processes each report
   - Logs are saved to `recent_reports_fetcher.log`

### Expected Output

The script generates an Excel file named `recent_metabase_reports_YYYYMMDD_HHMMSS.xlsx` containing:

| Column | Description |
|--------|-------------|
| `report_id` | Unique Metabase report identifier |
| `report_name` | Human-readable report name |
| `description` | Report description (if available) |
| `sql_query` | Full SQL query text |
| `collection_id` | Numeric collection identifier |
| `collection_name` | Human-readable collection name |
| `created_at` | Report creation timestamp |
| `updated_at` | Last modification timestamp |
| `view_count_last_12_months` | Number of views in the last 12 months |

## How It Works

### 1. **View Log Analysis**
- Connects to `/api/view_log` endpoint
- Filters for card (report) views from the last 12 months
- Counts view frequency for each unique report

### 2. **Exclusion Processing**
- Loads previous results from Excel file
- Creates exclusion set from `report_id` column
- Ensures no duplicate processing

### 3. **Collection Mapping**
- Fetches all collections via `/api/collection`
- Creates ID-to-name mapping for human-readable output

### 4. **Report Details Fetching**
- Loops through target report IDs
- Fetches full details via `/api/card/:id`
- Filters for native SQL queries only
- Handles errors gracefully

## Configuration Options

### Rate Limiting
The default API delay is 500ms between calls. To modify:

```python
# In the MetabaseRecentReportsFetcher.__init__ method
self.api_delay = 1.0  # 1 second delay
```

### Date Range
The default lookback period is 12 months. To modify:

```python
# In the MetabaseRecentReportsFetcher.__init__ method
self.twelve_months_ago = datetime.now() - timedelta(days=180)  # 6 months
```

### Batch Size
The view log fetch limit is 10,000 records. To modify:

```python
# In the fetch_view_logs method
params = {
    'start': start_timestamp,
    'limit': 20000  # Increase limit
}
```

## Error Handling

### Common Issues and Solutions

**❌ "Previous results file not found"**
- Ensure `metabase_reports_detailed_20250731_122354.xlsx` exists in the current directory
- Update the filename in the script if using a different file

**❌ "API request failed"**
- Check your Metabase URL format (include https://)
- Verify your API key is valid and has read permissions
- Ensure your Metabase instance is accessible

**❌ "No new reports found"**
- All recently viewed reports may have been previously processed
- Consider expanding the date range or checking view log data

### Logging
Detailed logs are saved to `recent_reports_fetcher.log` including:
- API request details
- Processing progress
- Error messages and stack traces
- Summary statistics

## Security Considerations

### API Key Safety
- API keys are input using `getpass` (not displayed on screen)
- Keys are only stored in memory during execution
- No persistent storage of credentials

### Read-Only Operations
- Multiple safety checks enforce GET-only requests
- Explicit comments in code confirming read-only operations
- No functionality for data modification

## Performance Notes

### Expected Processing Times
- **View log fetch:** 5-30 seconds (depending on data volume)
- **Report processing:** 0.5-1 second per report
- **Total time:** Varies based on number of new reports found

### Memory Usage
- Minimal memory footprint
- Processes reports one at a time
- Suitable for large datasets

## Integration with Existing Workflow

This script is designed to work alongside your existing Metabase analysis pipeline:

1. **Run this script** to identify new reports
2. **Feed results** into your business context generation tools
3. **Combine with previous results** for comprehensive analysis

## Troubleshooting

### Debug Mode
To enable verbose logging, modify the logging level:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

### API Testing
To test API connectivity without full processing:

```python
# Add this to the main() function for testing
fetcher = MetabaseRecentReportsFetcher(base_url, api_key)
collections = fetcher.fetch_collections_mapping()
print(f"Successfully connected! Found {len(collections)} collections.")
```

## Support

For issues or questions:
1. Check the log file for detailed error messages
2. Verify all prerequisites are installed
3. Ensure Metabase instance accessibility
4. Review the safety protocol compliance

---

**Remember:** This tool operates under strict read-only protocols to ensure the safety of your production Metabase instance. 