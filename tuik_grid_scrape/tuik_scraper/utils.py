import pandas as pd
import os
from pathlib import Path


def save_to_csv(data, path):
    """
    Appends to CSV if exists; creates otherwise.
    Deduplicates by 'id' (keeps first occurrence).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for item in data:
        # coords_to_wkt should return WKT string for geometry
        item['coordinates'] = coords_to_wkt(item['coordinates'])
        flat = {
            'id': item['id'],
            'timestamp': item['timestamp'],
            'geometry': item['coordinates'],
            'lon_lat': f"POINT({item.get('lon')} {item.get('lat')})",
        }
        # include all properties (make sure it's a dict)
        props = item.get('properties', {})
        if isinstance(props, dict):
            flat.update(props)
        rows.append(flat)

    new_df = pd.DataFrame(rows)

    if not path.exists():
        new_df.to_csv(path, index=False, encoding='utf-8')
        print(f"✅ Created and saved {len(new_df)} rows to {path}")
        return

    # Merge/dedupe
    try:
        existing_df = pd.read_csv(path, dtype=str)  # keep types stable for concat
    except Exception as e:
        print(f"❌ Failed to read existing CSV: {e}")
        return

    # Cast new_df 'id' to str as well to match dtype
    if 'id' in new_df.columns:
        new_df['id'] = new_df['id'].astype(str)

    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    before = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset='id', keep='first')

    # Keep a stable column order: existing + any new columns at the end
    cols = list(existing_df.columns) + [c for c in combined_df.columns if c not in existing_df.columns]
    combined_df = combined_df.reindex(columns=cols)

    combined_df.to_csv(path, index=False, encoding='utf-8')
    print(f"🧹 Merged, deduplicated ({before - len(combined_df)} removed) → {len(combined_df)} total rows")



def coords_to_wkt(coords):
    coords = coords[0]
    return "POLYGON((" + ", ".join([f"{x} {y}" for x, y in coords]) + "))"

def deduplicate_csv(path):
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return

    df = pd.read_csv(path)
    original_len = len(df)

    # Drop exact duplicate rows across all columns
    df = df.drop_duplicates()

    df.to_csv(path, index=False)
    if original_len - len(df) == 0:
        print("No duplicates found")
    else:
        print(f"🧹 Removed {original_len - len(df)} duplicates — {len(df)} rows remain in {path}")