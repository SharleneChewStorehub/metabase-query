# Metabase Active Reports Fetcher

A Python script that fetches Metabase reports that have been actively used (queried, viewed, or accessed) within the last 12 months, including detailed usage statistics.

## 🔒 Safety Protocol

**CRITICAL SAFETY MEASURE:** This script performs **READ-ONLY operations ONLY** using exclusively GET requests to the Metabase API. It will never create, modify, archive, or delete any reports, dashboards, or collections.

## ✨ Features

- **Activity-Based Filtering**: Only retrieves reports that have been used in the last 12 months
- **Usage Statistics**: Includes a count of how many times each report was accessed
- **Same Data Structure**: Maintains all the same columns as your existing Excel file
- **Enhanced Output**: Adds usage statistics while preserving original data format
- **Progress Tracking**: Real-time progress updates during processing
- **Error Handling**: Robust error handling with detailed logging
- **Configurable**: Customizable minimum usage thresholds

## 📋 Output Columns

The script generates an Excel file with the following columns:

1. `report_id` - Unique identifier for the report
2. `report_name` - Name of the report
3. `description` - Report description
4. `sql_query` - The actual SQL query or GUI query definition
5. `created_at` - When the report was created
6. `updated_at` - When the report was last updated
7. `collection_id` - ID of the collection containing the report
8. `database_id` - ID of the database the report queries
9. `query_type` - Type of query (native, query, etc.)
10. **`usage_count_last_12_months`** - ⭐ **NEW**: Number of times the report was used in the last 12 months

## 🚀 Quick Start

### 1. Setup Configuration

Ensure you have a `metabase_config.env` file with your Metabase credentials:

```env
METABASE_BASE_URL=https://your-metabase-instance.com
METABASE_API_KEY=your-api-key-here
API_DELAY_SECONDS=0.5
REQUEST_TIMEOUT_SECONDS=30
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Script

**Basic usage (minimum 1 usage):**
```bash
python metabase_active_reports_fetcher.py
```

**Custom minimum usage threshold:**
```bash
python metabase_active_reports_fetcher.py --min-usage 5
```

**Specify output file:**
```bash
python metabase_active_reports_fetcher.py --output my_active_reports.xlsx
```

**All options:**
```bash
python metabase_active_reports_fetcher.py \
    --min-usage 3 \
    --config custom_config.env \
    --output active_reports_2024.xlsx
```

## 📊 Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--min-usage` | 1 | Minimum number of times a report must have been used to be included |
| `--config` | `metabase_config.env` | Path to configuration file |
| `--output` | Auto-generated | Custom output Excel file path |

## 📈 What Gets Analyzed

The script analyzes usage from two main sources:

1. **General Activity Data** (`/api/activity`): Captures various interactions with reports
2. **Recent Views Data** (`/api/activity/recent_views`): Captures recent view activities

### Activity Time Range
- **Start Date**: 12 months ago from today
- **End Date**: Today
- Only activities within this range are counted

## 📄 Output Structure

The script generates an Excel file with multiple sheets:

### Sheet 1: "Active Reports (12 Months)"
- Contains all reports that meet the minimum usage criteria
- Sorted by usage count (most used first)
- Includes all original columns plus usage statistics

### Sheet 2: "Failed Fetches" (if any)
- Lists any reports that couldn't be fetched
- Includes error details for troubleshooting

### Sheet 3: "Summary"
- Processing statistics
- Date range information
- Usage summary metrics

## 🔍 Sample Output

```
📋 SAMPLE ACTIVE REPORTS (5 of 234 reports):
====================================================================================================

🔸 Report #1:
   ID: 2455
   Name: (Adhoc: Eddon) - # and GMV of Cancelled Orders that used Universal Promo...
   Usage (12 months): 47 times
   Last Updated: 2023-09-06T08:22:21.414717Z
   Query Type: native

🔸 Report #2:
   ID: 2454
   Name: (Adhoc: Eddon) - # of Universal Promo Code Applications and GMV...
   Usage (12 months): 31 times
   Last Updated: 2024-01-16T03:23:08.808941Z
   Query Type: native
```

## ⚙️ How It Works

1. **Connection Test**: Verifies API connectivity and credentials
2. **Activity Fetch**: Retrieves activity data from Metabase API
3. **Usage Analysis**: Counts usage instances for each report in the last 12 months
4. **Filtering**: Selects only reports meeting minimum usage criteria
5. **Detail Fetch**: Retrieves complete details for active reports
6. **Excel Generation**: Creates comprehensive Excel output with statistics

## 🛡️ Safety Features

- **Read-Only Operations**: Only GET requests are made
- **Rate Limiting**: Configurable delays between API calls
- **Error Recovery**: Continues processing even if individual requests fail
- **Progress Tracking**: Shows real-time progress for long-running operations
- **Comprehensive Logging**: Detailed logs for troubleshooting

## 🔧 Configuration Options

### Environment Variables

```env
# Required
METABASE_BASE_URL=https://your-metabase-instance.com
METABASE_API_KEY=your-api-key-here

# Optional
API_DELAY_SECONDS=0.5          # Delay between API calls
REQUEST_TIMEOUT_SECONDS=30     # Request timeout
```

### Script Parameters

```python
# In the script, you can modify:
self.start_date = self.end_date - timedelta(days=365)  # Change date range
```

## 📊 Performance Considerations

- **Processing Time**: Depends on number of active reports (typically 1-5 minutes)
- **API Rate Limiting**: Built-in delays to respect Metabase API limits
- **Memory Usage**: Efficient processing of large datasets
- **Error Resilience**: Continues processing even if some reports fail

## 🔍 Troubleshooting

### Common Issues

1. **No reports found**: Check if date range or minimum usage is too restrictive
2. **Connection errors**: Verify API key and Metabase URL
3. **Permission errors**: Ensure API key has sufficient read permissions

### Debug Information

The script generates detailed logs in `metabase_active_reports_fetcher.log`:

```bash
tail -f metabase_active_reports_fetcher.log
```

## 📝 Comparison with Original Script

| Feature | Original Script | Active Reports Script |
|---------|----------------|----------------------|
| **Data Source** | All reports from Excel file | Active reports from API |
| **Filtering** | None | Last 12 months usage |
| **Usage Data** | ❌ No | ✅ Yes |
| **Performance** | Batch processing | Smart filtering first |
| **Output** | All reports | Only actively used reports |

## 🎯 Use Cases

- **Resource Optimization**: Identify which reports are actually being used
- **Cleanup Planning**: Find unused reports for potential archival
- **Usage Analytics**: Understand report consumption patterns
- **Performance Monitoring**: Focus optimization efforts on high-usage reports
- **License Planning**: Understand actual vs. theoretical usage

## 🔄 Regular Usage

For regular monitoring, consider:

1. **Monthly Reports**: Run monthly to track usage trends
2. **Automated Scheduling**: Set up cron jobs for regular execution
3. **Usage Tracking**: Compare usage over time to identify trends
4. **Cleanup Cycles**: Use results to guide periodic cleanup activities

## 🚨 Important Notes

- **API Limits**: Respects Metabase API rate limits with built-in delays
- **Data Accuracy**: Usage counts depend on Metabase activity logging
- **Time Zone**: Uses server time zone for activity analysis
- **Permissions**: Requires read access to all reports you want to analyze

This script provides a powerful way to understand which of your Metabase reports are actually being used, helping you focus maintenance and optimization efforts where they matter most. 