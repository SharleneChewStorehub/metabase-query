# Metabase API Report Fetcher - Setup Guide

## 🚀 Quick Start

This script fetches detailed report information from your Metabase instance using the Report IDs from your Excel file.

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Metabase Credentials

**Option A: Interactive Setup (Recommended)**
```bash
python setup_metabase_config.py
```

**Option B: Manual Setup**
Edit `metabase_config.env` with your credentials:
```env
METABASE_BASE_URL=https://your-metabase-instance.com
METABASE_API_KEY=your-api-key-here
API_DELAY_SECONDS=0.5
REQUEST_TIMEOUT_SECONDS=30
```

### 3. Run the Fetcher

```bash
python metabase_api_fetcher.py
```

## 🔑 Getting Your Metabase API Key

1. Log into your Metabase instance
2. Go to **Settings** (gear icon) → **Admin Settings**
3. Navigate to **Settings** → **General** → **API Keys**
4. Click **Create API Key**
5. Give it a descriptive name (e.g., "Report Analysis Script")
6. Copy the generated key

## 📊 What the Script Does

1. **Reads Excel File**: Loads Report IDs from `metabase_reports_analysis.xlsx`
2. **Tests Connection**: Verifies your Metabase credentials
3. **Fetches Reports**: Gets detailed information for each report:
   - Report Name
   - Description
   - Complete SQL Query
   - Metadata (created/updated dates, collection info)
4. **Handles Errors**: Gracefully manages deleted/archived reports
5. **Saves Results**: Outputs to Excel with multiple sheets:
   - **Report Details**: Successfully fetched reports
   - **Failed Fetches**: Reports that couldn't be fetched
   - **Summary**: Statistics and processing info

## ⚙️ Configuration Options

- **API_DELAY_SECONDS**: Delay between requests (default: 0.5s)
- **REQUEST_TIMEOUT_SECONDS**: Timeout for each request (default: 30s)

## 🛡️ Security Best Practices

- Never commit `metabase_config.env` to version control
- Use a dedicated API key with minimal required permissions
- Monitor API usage to stay within rate limits

## 📝 Output Files

- **metabase_reports_detailed_YYYYMMDD_HHMMSS.xlsx**: Main results
- **metabase_api_fetcher.log**: Detailed processing log

## 🔧 Troubleshooting

### Connection Issues
- Verify your Metabase URL (include `https://`)
- Check API key is valid and has proper permissions
- Ensure network connectivity to Metabase instance

### Missing Reports
- Some Report IDs may be deleted/archived in Metabase
- Check the "Failed Fetches" sheet for details
- These are logged as warnings, not errors

### Performance
- Processing 1,549 reports takes ~13 minutes with default 0.5s delay
- Reduce delay for faster processing (but respect server limits)
- Use test mode first to verify everything works

## 🧪 Testing

Start with test mode to verify configuration:
```bash
python metabase_api_fetcher.py
# Choose 'y' when prompted for test mode
```

This processes only the first 10 reports to verify everything works correctly.

## 📈 Expected Processing Time

- **Test Mode (10 reports)**: ~5 seconds
- **Full Dataset (1,549 reports)**: ~13 minutes
- **Rate**: ~120 reports/minute with 0.5s delay

## 🆘 Need Help?

Check the log file (`metabase_api_fetcher.log`) for detailed error messages and processing information. 