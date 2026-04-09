# app colors
# #027380, #ffffff, #3e858d, #4b4c43, #53554b

import json
import zipfile
from io import BytesIO

import pandas as pd
import streamlit as st


def parse_csv_file(uploaded_file):
    try:
        return pd.read_csv(uploaded_file)
    except Exception as exc:
        raise ValueError(f"Unable to parse CSV: {exc}") from exc


def parse_json_file(uploaded_file):
    try:
        text = uploaded_file.read().decode("utf-8")
        return json.loads(text)
    except Exception as exc:
        raise ValueError(f"Unable to parse JSON/GeoJSON: {exc}") from exc


def detect_dataset_format(uploaded_file):
    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        return "csv"
    if filename.endswith(".geojson") or filename.endswith(".json"):
        return "geojson"
    return "unknown"


def geojson_feature_id(feature, id_field):
    if not isinstance(feature, dict):
        return None
    if "properties" in feature and isinstance(feature["properties"], dict):
        value = feature["properties"].get(id_field)
        if value is not None:
            return value
    if id_field == "id" and feature.get("id") is not None:
        return feature["id"]
    return feature.get("id")


def extract_ids_from_dataframe(df, id_field):
    if id_field not in df.columns:
        raise ValueError(f"ID field '{id_field}' not found in CSV columns: {list(df.columns)}")
    return set(
        df[id_field]
        .astype(str)
        .str.strip()
        .replace(["None", "nan", ""], pd.NA)
        .dropna()
    )


def extract_ids_from_geojson(data, id_field):
    if not isinstance(data, dict) or "features" not in data or not isinstance(data["features"], list):
        raise ValueError("GeoJSON must contain a FeatureCollection with a 'features' list.")
    ids = set()
    for feature in data["features"]:
        value = geojson_feature_id(feature, id_field)
        if value is None:
            continue
        string_value = str(value).strip()
        if string_value:
            ids.add(string_value)
    return ids


def load_dataset(uploaded_file):
    file_format = detect_dataset_format(uploaded_file)
    uploaded_file.seek(0)
    if file_format == "csv":
        return "csv", parse_csv_file(uploaded_file)
    if file_format == "geojson":
        return "geojson", parse_json_file(uploaded_file)
    raise ValueError(
        "Unsupported file type. Upload a .csv, .json, or .geojson file for the dataset."
    )


def filter_unmigrated(full_dataset, full_format, migrated_ids, id_field):
    if full_format == "csv":
        df = full_dataset.copy()
        if id_field not in df.columns:
            raise ValueError(f"ID field '{id_field}' not found in all-assets dataset columns.")
        mask = ~df[id_field].astype(str).str.strip().isin(migrated_ids)
        return df.loc[mask].reset_index(drop=True)

    if full_format == "geojson":
        output = {**full_dataset}
        features = []
        for feature in full_dataset.get("features", []):
            feature_id = geojson_feature_id(feature, id_field)
            if feature_id is None:
                # preserve any feature without an ID; assume unmigrated if it cannot be matched
                features.append(feature)
                continue
            if str(feature_id).strip() not in migrated_ids:
                features.append(feature)
        output["features"] = features
        return output

    raise ValueError("Unsupported full dataset format for filtering.")


def build_download_bytes(dataset, dataset_format):
    if dataset_format == "csv":
        return dataset.to_csv(index=False).encode("utf-8")
    if dataset_format == "geojson":
        return json.dumps(dataset, indent=2).encode("utf-8")
    raise ValueError("Unsupported export format.")


def main():
    st.set_page_config(
        page_title="Unmigrated Asset Extractor",
        page_icon="assets/sucafina.svg",
        layout="wide", 
    )

    st.title("Unmigrated Asset Extractor")
    st.markdown(
        "Upload the recent dataset that includes all assets and the previously migrated asset dataset. "
        "This tool exports only the assets in the full dataset that are not present in the migrated dataset."
    )

    with st.expander("How it works", expanded=False):
        st.markdown(
            "1. Upload the recently downloaded dataset from TIS containing every asset.\n"
            "2. Upload the dataset of already migrated assets. This file may be named 'lot1' for the first lot of migrated assets or lot1-n for subsequent lots up to the nth lot. In some cases it may prefixed with a Supply Chain Code, forexample, 'COOX-lot1' or 'COOX-lot1-n'.\n"
            "3. Enter the asset identifier field name used in both datasets (for GeoJSON, the field is searched inside feature properties or feature.id).\n"
            "4. Download the filtered dataset containing only unmigrated assets."
        )

    col1, col2 = st.columns(2)
    with col1:
        full_file = st.file_uploader(
            "Upload full assets dataset",
            type=["csv", "json", "geojson"],
            key="full_dataset",
        )
    with col2:
        migrated_file = st.file_uploader(
            "Upload migrated assets dataset",
            type=["csv", "json", "geojson"],
            key="migrated_dataset",
        )

    # id_col, code_col, is_new_supply_chain = st.columns(3)
    # id_field = id_col.text_input("Asset ID field name", value="ID")
    # supply_chain_code = code_col.text_input("Supply Chain Code", value="")
    # is_new_supply_chain = is_new_supply_chain.checkbox("Is New Supply Chain?", value=False)

    id_col, code_and_supply_chain_col = st.columns(2)
    id_field = id_col.text_input("Asset ID field name", value="ID") 
    supply_chain_code = code_and_supply_chain_col.text_input("Supply Chain Code", value="")
    is_new_supply_chain = code_and_supply_chain_col.checkbox("Is New Supply Chain? (Check if this is the first migration for this supply chain)", value=False)
    

    if not full_file:
        st.warning("Please upload the all-assets dataset to extract unmigrated assets.")
        return

    if not is_new_supply_chain and not migrated_file:
        st.warning("Please upload the migrated-assets dataset or check 'Is New Supply Chain?' if this is the first migration for this supply chain.")
        return

    if is_new_supply_chain and migrated_file:
        st.error("A migrated assets dataset should not be uploaded when 'Is New Supply Chain?' is checked. Please remove the migrated dataset file and try again.")
        return

    try:
        full_format, full_dataset = load_dataset(full_file)

        migrated_ids = set()
        if not is_new_supply_chain:
            migrated_format, migrated_dataset = load_dataset(migrated_file)
            if migrated_format == "csv":
                migrated_ids = extract_ids_from_dataframe(migrated_dataset, id_field)
            else:
                migrated_ids = extract_ids_from_geojson(migrated_dataset, id_field)

        unmigrated = filter_unmigrated(full_dataset, full_format, migrated_ids, id_field)

        # Calculate statistics
        if full_format == "csv":
            total_assets = len(full_dataset)
            new_assets = len(unmigrated)
        else:
            total_assets = len(full_dataset["features"])
            new_assets = len(unmigrated["features"])
        previously_migrated = len(migrated_ids)

        st.success(f"Unmigrated asset extraction complete. Total Assets: {total_assets}, Previously Migrated: {previously_migrated}, New Assets to Migrate: {new_assets}")

        # Prepare data for display and export
        if full_format == "csv":
            df = unmigrated
        else:
            df = pd.DataFrame([f.get("properties", {}) for f in unmigrated.get("features", [])])

        st.write(f"Found {len(df)} unmigrated records.")
        st.dataframe(df)

        if not supply_chain_code.strip():
            st.warning("Please enter a Supply Chain Code to download the exported data.")
            return

        # Prepare data for both formats
        if full_format == "csv":
            geojson_data = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": row.to_dict(),
                        "geometry": None
                    } for _, row in df.iterrows()
                ]
            }
        else:
            geojson_data = unmigrated

        # Generate file contents
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        geojson_bytes = json.dumps(geojson_data, indent=2).encode("utf-8")
        stats_text = f"Total Assets: {total_assets}\nPreviously Migrated: {previously_migrated}\nNew Assets to Migrate: {new_assets}"
        txt_bytes = stats_text.encode("utf-8")

        code_name = supply_chain_code.strip() or "unmigrated_assets"
        safe_code_name = code_name.replace(" ", "_")

        # Create ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(f"{safe_code_name}.csv", csv_bytes)
            zip_file.writestr(f"{safe_code_name}.geojson", geojson_bytes)
            zip_file.writestr(f"{safe_code_name}.txt", txt_bytes)
        zip_buffer.seek(0)

        st.download_button(
            label="Download unmigrated assets as ZIP",
            data=zip_buffer.getvalue(),
            file_name=f"{safe_code_name}.zip",
            mime="application/zip",
        )
    except Exception as exc:
        st.error(f"Error extracting unmigrated assets: {exc}")


if __name__ == "__main__":
    main()
