import pandas as pd

def save_to_csv(data, path):
    rows = []
    for item in data:
        flat = {
            'id': item['id'],
            'timestamp': item['timestamp'],
            'geometry': item['coordinates'],
        }
        flat.update(item['properties'])
        rows.append(flat)

    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    print(f"✅ Saved {len(df)} rows to {path}")
