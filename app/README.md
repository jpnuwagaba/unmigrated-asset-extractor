# Unmigrated Asset Extractor - Documentation

## Overview

The Unmigrated Asset Extractor is a Streamlit web application designed to identify and extract assets that have not yet been migrated from a full dataset. It compares a complete asset dataset against a dataset of already migrated assets, using a specified ID field for matching.

## Features

- **Multi-format Support**: Accepts CSV and GeoJSON files for both full and migrated datasets.
- **Flexible ID Matching**: Supports custom ID field names for asset identification.
- **Unified Preview**: Displays extracted assets in a tabular format for easy review.
- **Comprehensive Export**: Downloads unmigrated assets in both CSV and GeoJSON formats, plus a statistics report, all packaged in a ZIP file.
- **Custom Naming**: Allows specification of a Supply Chain Code for personalized file naming.

## Usage

### Prerequisites

- Python 3.7 or higher
- Required packages: `streamlit`, `pandas` (install via `pip install -r requirements.txt`)

### Running the Application

1. Start the app: `streamlit run app.py`
2. Open the provided URL in your web browser.

### Step-by-Step Guide

1. **Upload Datasets**:
   - **Full Assets Dataset**: Upload the complete dataset containing all assets (CSV or GeoJSON).
   - **Migrated Assets Dataset**: Upload the dataset of assets that have already been migrated (CSV or GeoJSON).

2. **Configure Fields**:
   - **Asset ID Field Name**: Enter the name of the field used to identify assets (default: "ID"). For GeoJSON, this field is searched in feature properties or feature.id.
   - **Supply Chain Code**: (Optional) Enter a code (e.g., "COOX-lot1") to customize the exported file names.

3. **Process and Review**:
   - The app will extract unmigrated assets and display statistics: Total Assets, Previously Migrated, and New Assets to Migrate.
   - Review the extracted assets in the tabular preview.

4. **Download Results**:
   - Click "Download unmigrated assets as ZIP" to get a package containing:
     - `{SupplyChainCode}.csv`: Unmigrated assets in CSV format
     - `{SupplyChainCode}.geojson`: Unmigrated assets in GeoJSON format
     - `{SupplyChainCode}.txt`: Statistics report

## Input Requirements

### File Formats
- **CSV**: Standard comma-separated values with headers.
- **GeoJSON**: FeatureCollection with features containing properties and optional geometry.

### ID Field
- Must exist in both datasets.
- Used for exact string matching to identify migrated vs. unmigrated assets.
- For GeoJSON, checked in `feature.properties[id_field]` or `feature.id`.

### Data Assumptions
- Assets without matching IDs are considered unmigrated.
- Empty or null ID values are ignored.

## Output

### ZIP Package Contents
- **CSV File**: Tabular data of unmigrated assets.
- **GeoJSON File**: Spatial data of unmigrated assets (if applicable).
- **Statistics File**: Text report with migration counts.

### File Naming
- If Supply Chain Code is provided, files are named `{Code}.csv`, `{Code}.geojson`, `{Code}.txt`.
- Default: `unmigrated_assets.*`

## Error Handling

- Validates file formats and ID field presence.
- Displays error messages for invalid inputs or processing failures.
- Ensures data integrity during extraction and conversion.

## Limitations

- Assumes consistent ID field naming across datasets.
- GeoJSON to CSV conversion extracts only properties; geometry is not included in CSV.
- Large datasets may impact performance; consider data size limits.

## Support

For issues or questions, please refer to the application error messages or contact the development team.