import pandas as pd
import os
from pathlib import Path
import matplotlib.pyplot as plt


import os
import pandas as pd
from pathlib import Path
from datetime import datetime

MAX_BYTES = 2_000_000_000  # ~2 GB per shard, tweak as needed

def save_to_csv(data, path):
    """
    Fast, low-IO appender:
      - de-dupes current batch by 'id'
      - appends to CSV without loading existing file
      - rotates to new shard if file too big
      - OPTIONAL: write gzip shards instead of a single CSV
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # --- flatten current batch ---
    rows = []
    for item in data:
        item['coordinates'] = coords_to_wkt(item['coordinates'])
        flat = {
            'id': item['id'],
            'timestamp': item['timestamp'],
            'geometry': item['coordinates'],
            'lon_lat': f"POINT({item.get('lon')} {item.get('lat')})",
        }
        props = item.get('properties', {})
        if isinstance(props, dict):
            flat.update(props)
        rows.append(flat)

    if not rows:
        print("ℹ️ Nothing to write.")
        return

    df = pd.DataFrame(rows)

    # de-dupe within the batch (cheap)
    if 'id' in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset='id', keep='first')
        if len(df) < before:
            print(f"🧹 Batch de-dup: {before - len(df)} duplicates removed in-memory")

    # --- rotation helper ---
    def ensure_target_file(base_path: Path) -> Path:
        # rotate if file exists and exceeds limit
        if base_path.exists() and base_path.stat().st_size >= MAX_BYTES:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated = base_path.with_name(base_path.stem + f"_{ts}.csv")
            print(f"🔁 Rotating to {rotated.name} (size limit reached)")
            return rotated
        return base_path

    # Choose one of the two output styles:

    # Single CSV that appends & rotates:
    target = ensure_target_file(path)
    write_header = not target.exists()
    df.to_csv(target, mode='a', header=write_header, index=False, encoding='utf-8')
    print(f"💾 Appended {len(df)} rows → {target}")






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

def visualize_scraped_points(polygons,points,il):
    # 3) Visualize
    fig, ax = plt.subplots()
    fig.set_figheight(30)
    fig.set_figwidth(30)

    # draw polygons
    for poly in polygons:
        x, y = poly.exterior.xy
        ax.plot(x, y)
        for interior in poly.interiors:  # draw holes if any
            xi, yi = interior.xy
            ax.plot(xi, yi)

    # draw points
    if points:
        xs, ys = zip(*points[0])
        ax.scatter(xs, ys, s=4)  # small size so it’s readable

    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title(f'Systematic points inside {il[0]}')
    print(f"Total points: {len(points[0])}")
    plt.show()
