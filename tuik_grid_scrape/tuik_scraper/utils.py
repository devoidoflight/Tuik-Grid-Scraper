import pandas as pd
import os

import pandas as pd
import os

import pandas as pd
import os

def save_to_csv(data, path):
    rows = []
    for item in data:
        item['coordinates'] = coords_to_wkt(item['coordinates'])
        flat = {
            'id': item['id'],
            'timestamp': item['timestamp'],
            'geometry': item['coordinates'],
            'lon_lat': f"POINT({item.get('lon')} {item.get('lat')})"
        }
        flat.update(item['properties'])
        rows.append(flat)

    new_df = pd.DataFrame(rows)

    if not os.path.exists(path):
        new_df.to_csv(path, index=False)
        print(f"✅ Created and saved {len(new_df)} rows to {path}")
    else:
        try:
            existing_df = pd.read_csv(path, dtype=str)
        except Exception as e:
            print(f"❌ Failed to read existing CSV: {e}")
            return

        # Combine and deduplicate by 'id'
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        before = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset='id')  # Deduplicate by ID only

        # Reindex to keep column consistency
        combined_df = combined_df.reindex(sorted(combined_df.columns), axis=1)

        combined_df.to_csv(path, index=False)
        print(f"🧹 Merged, deduplicated ({before - len(combined_df)} duplicates removed) → {len(combined_df)} total rows")




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