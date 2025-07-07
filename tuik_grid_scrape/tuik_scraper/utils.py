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
        }
        flat.update(item['properties'])
        rows.append(flat)

    if not os.path.exists(path):
        # File doesn't exist → create and write with headers
        df = pd.DataFrame(rows)
        df.to_csv(path, index=False)
        print(f"✅ Created and saved {len(df)} rows to {path}")
    else:
        # File exists → append without header
        df = pd.DataFrame(rows)
        df.to_csv(path, mode='a', index=False, header=False)
        print(f"➕ Appended {len(df)} rows to {path}")

def coords_to_wkt(coords):
    coords = coords[0]
    return "POLYGON((" + ", ".join([f"{x} {y}" for x, y in coords]) + "))"
