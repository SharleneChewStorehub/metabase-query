#!/usr/bin/env python3
"""
Metabase Reports Excel Analyzer

A comprehensive Python script to read, analyze, and explore Excel files
using pandas and other data analysis libraries.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union
import warnings

# Suppress openpyxl warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

class ExcelAnalyzer:
    """
    A comprehensive Excel file analyzer using pandas for robust data analysis.
    """
    
    def __init__(self, file_path: str):
        """
        Initialize the Excel analyzer.
        
        Args:
            file_path (str): Path to the Excel file
        """
        self.file_path = Path(file_path)
        self.excel_data: Dict[str, pd.DataFrame] = {}
        self.sheet_info: Dict[str, dict] = {}
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
    
    def load_file(self) -> 'ExcelAnalyzer':
        """
        Load all worksheets from the Excel file.
        
        Returns:
            ExcelAnalyzer: Self for method chaining
        """
        try:
            print(f"📖 Loading Excel file: {self.file_path}")
            
            # Read all sheets
            self.excel_data = pd.read_excel(
                self.file_path, 
                sheet_name=None,  # Read all sheets
                engine='openpyxl'
            )
            
            # Collect metadata for each sheet
            for sheet_name, df in self.excel_data.items():
                self.sheet_info[sheet_name] = {
                    'shape': df.shape,
                    'columns': list(df.columns),
                    'dtypes': df.dtypes.to_dict(),
                    'memory_usage': df.memory_usage(deep=True).sum(),
                    'null_counts': df.isnull().sum().to_dict()
                }
            
            print(f"✅ Successfully loaded {len(self.excel_data)} worksheet(s)")
            return self
            
        except Exception as e:
            print(f"❌ Error loading Excel file: {str(e)}")
            raise
    
    def get_sheet_names(self) -> List[str]:
        """Get list of all worksheet names."""
        return list(self.excel_data.keys())
    
    def get_sheet_data(self, sheet_name: str) -> pd.DataFrame:
        """
        Get DataFrame for a specific worksheet.
        
        Args:
            sheet_name (str): Name of the worksheet
            
        Returns:
            pd.DataFrame: The worksheet data
        """
        if sheet_name not in self.excel_data:
            available_sheets = ", ".join(self.get_sheet_names())
            raise ValueError(f"Sheet '{sheet_name}' not found. Available sheets: {available_sheets}")
        
        return self.excel_data[sheet_name]
    
    def display_summary(self) -> None:
        """Display comprehensive summary of all worksheets."""
        print("\n📊 EXCEL FILE ANALYSIS SUMMARY")
        print("=" * 70)
        
        total_rows = sum(df.shape[0] for df in self.excel_data.values())
        total_cols = sum(df.shape[1] for df in self.excel_data.values())
        total_memory = sum(info['memory_usage'] for info in self.sheet_info.values())
        
        print(f"📁 File: {self.file_path.name}")
        print(f"📋 Total Sheets: {len(self.excel_data)}")
        print(f"📏 Total Rows: {total_rows:,}")
        print(f"📐 Total Columns: {total_cols}")
        print(f"💾 Memory Usage: {total_memory / 1024 / 1024:.2f} MB")
        print()
        
        for i, (sheet_name, info) in enumerate(self.sheet_info.items(), 1):
            rows, cols = info['shape']
            null_count = sum(info['null_counts'].values())
            
            print(f"{i}. 📄 Sheet: '{sheet_name}'")
            print(f"   📏 Dimensions: {rows:,} rows × {cols} columns")
            null_pct = (null_count/(rows*cols)*100) if rows > 0 and cols > 0 else 0
            print(f"   🚫 Null values: {null_count:,} ({null_pct:.1f}%)")
            
            if cols > 0:
                column_preview = info['columns'][:5]
                if len(info['columns']) > 5:
                    column_preview.append('...')
                print(f"   📋 Columns: {', '.join(map(str, column_preview))}")
            
            # Show data types summary
            dtype_counts = pd.Series(info['dtypes']).value_counts()
            dtype_summary = ", ".join([f"{count} {dtype}" for dtype, count in dtype_counts.items()])
            print(f"   🔢 Data Types: {dtype_summary}")
            print()
    
    def preview_sheet(self, sheet_name: str, max_rows: int = 5) -> None:
        """
        Display preview of a specific worksheet with enhanced formatting.
        
        Args:
            sheet_name (str): Name of the worksheet
            max_rows (int): Maximum number of rows to preview
        """
        print(f"\n🔍 DETAILED PREVIEW: '{sheet_name}'")
        print("=" * 70)
        
        df = self.get_sheet_data(sheet_name)
        
        if df.empty:
            print("📭 This worksheet is empty.")
            return
        
        # Basic info
        print(f"📏 Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
        print(f"💾 Memory: {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
        
        # Show first few rows
        print(f"\n📋 First {min(max_rows, len(df))} rows:")
        with pd.option_context('display.max_columns', 10, 'display.width', 120):
            print(df.head(max_rows))
        
        # Column info
        if len(df.columns) > 0:
            print(f"\n📊 Column Information:")
            for i, col in enumerate(df.columns[:10]):  # Show first 10 columns
                dtype = df[col].dtype
                null_count = df[col].isnull().sum()
                null_pct = (null_count / len(df)) * 100 if len(df) > 0 else 0
                unique_count = df[col].nunique()
                
                print(f"   {i+1:2d}. {col}: {dtype} | {null_count} nulls ({null_pct:.1f}%) | {unique_count} unique")
            
            if len(df.columns) > 10:
                print(f"   ... and {len(df.columns) - 10} more columns")
    
    def analyze_sheet(self, sheet_name: str) -> dict:
        """
        Perform comprehensive analysis of a worksheet.
        
        Args:
            sheet_name (str): Name of the worksheet
            
        Returns:
            dict: Analysis results
        """
        df = self.get_sheet_data(sheet_name)
        
        analysis = {
            'basic_stats': {},
            'data_quality': {},
            'column_analysis': {}
        }
        
        # Basic statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            analysis['basic_stats'] = df[numeric_cols].describe().to_dict()
        
        # Data quality assessment
        analysis['data_quality'] = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'duplicate_rows': df.duplicated().sum(),
            'completely_empty_rows': df.isnull().all(axis=1).sum(),
            'columns_with_nulls': (df.isnull().any()).sum(),
            'overall_null_percentage': (df.isnull().sum().sum() / df.size) * 100 if df.size > 0 else 0
        }
        
        # Per-column analysis
        for col in df.columns:
            series = df[col]
            analysis['column_analysis'][col] = {
                'dtype': str(series.dtype),
                'null_count': series.isnull().sum(),
                'null_percentage': (series.isnull().sum() / len(series)) * 100 if len(series) > 0 else 0,
                'unique_count': series.nunique(),
                'unique_percentage': (series.nunique() / len(series)) * 100 if len(series) > 0 else 0
            }
            
            # Add specific analysis based on data type
            if pd.api.types.is_numeric_dtype(series):
                analysis['column_analysis'][col].update({
                    'min': series.min(),
                    'max': series.max(),
                    'mean': series.mean(),
                    'std': series.std()
                })
            elif pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
                analysis['column_analysis'][col].update({
                    'most_common': series.value_counts().head(3).to_dict()
                })
        
        return analysis
    
    def search_values(self, search_term: str, case_sensitive: bool = False) -> pd.DataFrame:
        """
        Search for specific values across all worksheets.
        
        Args:
            search_term (str): Term to search for
            case_sensitive (bool): Whether search should be case sensitive
            
        Returns:
            pd.DataFrame: Search results with sheet, row, column, and value
        """
        results = []
        
        for sheet_name, df in self.excel_data.items():
            # Convert all data to string for searching
            df_str = df.astype(str)
            
            if not case_sensitive:
                search_term = search_term.lower()
                df_str = df_str.apply(lambda x: x.str.lower() if x.dtype == 'object' else x)
            
            # Find matches
            for col in df_str.columns:
                mask = df_str[col].str.contains(search_term, na=False, regex=False)
                matches = df[mask]
                
                for idx, row in matches.iterrows():
                    results.append({
                        'sheet': sheet_name,
                        'row': idx + 2,  # +2 because Excel rows start at 1 and we have headers
                        'column': col,
                        'value': row[col]
                    })
        
        return pd.DataFrame(results)
    
    def export_to_json(self, sheet_name: str, output_path: Optional[str] = None) -> str:
        """
        Export a worksheet to JSON format.
        
        Args:
            sheet_name (str): Name of the worksheet
            output_path (str, optional): Output file path
            
        Returns:
            str: Path to the created JSON file
        """
        df = self.get_sheet_data(sheet_name)
        
        if output_path is None:
            safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in sheet_name)
            output_path = f"{safe_name}.json"
        
        # Convert DataFrame to JSON with proper handling of NaN values
        df.to_json(output_path, orient='records', indent=2, force_ascii=False)
        
        print(f"💾 Exported '{sheet_name}' to {output_path}")
        return output_path
    
    def export_to_csv(self, sheet_name: str, output_path: Optional[str] = None) -> str:
        """
        Export a worksheet to CSV format.
        
        Args:
            sheet_name (str): Name of the worksheet
            output_path (str, optional): Output file path
            
        Returns:
            str: Path to the created CSV file
        """
        df = self.get_sheet_data(sheet_name)
        
        if output_path is None:
            safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in sheet_name)
            output_path = f"{safe_name}.csv"
        
        df.to_csv(output_path, index=False)
        
        print(f"💾 Exported '{sheet_name}' to {output_path}")
        return output_path
    
    def create_summary_report(self, output_path: str = "excel_analysis_report.txt") -> None:
        """
        Create a comprehensive text report of the Excel file analysis.
        
        Args:
            output_path (str): Path for the output report
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("EXCEL FILE ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"File: {self.file_path}\n")
            f.write(f"Generated: {pd.Timestamp.now()}\n\n")
            
            for sheet_name in self.get_sheet_names():
                f.write(f"\nSHEET: {sheet_name}\n")
                f.write("-" * 30 + "\n")
                
                analysis = self.analyze_sheet(sheet_name)
                
                # Basic info
                dq = analysis['data_quality']
                f.write(f"Dimensions: {dq['total_rows']} rows × {dq['total_columns']} columns\n")
                f.write(f"Duplicate rows: {dq['duplicate_rows']}\n")
                f.write(f"Empty rows: {dq['completely_empty_rows']}\n")
                f.write(f"Overall null percentage: {dq['overall_null_percentage']:.2f}%\n\n")
                
                # Column details
                f.write("COLUMNS:\n")
                for col, col_info in analysis['column_analysis'].items():
                    f.write(f"  {col}: {col_info['dtype']} | ")
                    f.write(f"{col_info['null_percentage']:.1f}% null | ")
                    f.write(f"{col_info['unique_count']} unique\n")
        
        print(f"📄 Analysis report saved to {output_path}")


def main():
    """Main execution function."""
    excel_file = "./metabase_reports_analysis.xlsx"
    
    try:
        # Create analyzer instance and load file
        analyzer = ExcelAnalyzer(excel_file)
        analyzer.load_file()
        
        # Display comprehensive summary
        analyzer.display_summary()
        
        # Preview each worksheet
        for sheet_name in analyzer.get_sheet_names():
            analyzer.preview_sheet(sheet_name, max_rows=3)
        
        # Example: Detailed analysis of first sheet
        if analyzer.get_sheet_names():
            first_sheet = analyzer.get_sheet_names()[0]
            print(f"\n🔬 DETAILED ANALYSIS: '{first_sheet}'")
            print("=" * 70)
            analysis = analyzer.analyze_sheet(first_sheet)
            
            # Print data quality summary
            dq = analysis['data_quality']
            print(f"📊 Data Quality Summary:")
            print(f"   Duplicate rows: {dq['duplicate_rows']}")
            print(f"   Empty rows: {dq['completely_empty_rows']}")
            print(f"   Columns with nulls: {dq['columns_with_nulls']}")
            print(f"   Overall null percentage: {dq['overall_null_percentage']:.2f}%")
        
        # Uncomment these sections as needed:
        
        # # Export first sheet to CSV
        # if analyzer.get_sheet_names():
        #     analyzer.export_to_csv(analyzer.get_sheet_names()[0])
        
        # # Search for specific values
        # search_results = analyzer.search_values('metabase', case_sensitive=False)
        # if not search_results.empty:
        #     print("\n🔍 Search Results for 'metabase':")
        #     print(search_results.head(10))
        
        # # Create comprehensive report
        # analyzer.create_summary_report()
        
        print("\n✨ Analysis complete!")
        
    except Exception as e:
        print(f"💥 Analysis failed: {str(e)}")
        raise


if __name__ == "__main__":
    main() 