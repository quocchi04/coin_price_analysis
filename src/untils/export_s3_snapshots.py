import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def parse_timestamp(value, source_tz, timezone_map):
    value = value.strip()
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if timestamp.tzinfo is None:
        timezone_name = timezone_map.get(value, source_tz)
        if not timezone_name:
            raise ValueError(f"Chưa xác định múi giờ cho {value!r}")
        timestamp = timestamp.replace(tzinfo=ZoneInfo(timezone_name))

    return timestamp.astimezone(timezone.utc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_dir", type=Path)
    timezone_options = parser.add_mutually_exclusive_group()
    timezone_options.add_argument("--source-tz")
    timezone_options.add_argument("--timezone-map", type=Path)
    parser.add_argument("--single-snapshot", action="store_true")
    args = parser.parse_args()

    timezone_map = {}
    if args.timezone_map:
        timezone_map = json.loads(args.timezone_map.read_text(encoding="utf-8"))

    snapshots = defaultdict(dict)
    input_rows = 0

    with args.input_csv.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames or []
        if not {"id", "time_collected"}.issubset(columns):
            raise ValueError("CSV phải có các cột id và time_collected")

        for row in reader:
            input_rows += 1
            coin_id = (row["id"] or "").strip()
            timestamp_text = (row["time_collected"] or "").strip()
            if not coin_id or not timestamp_text:
                raise ValueError(f"Dòng {reader.line_num} thiếu id hoặc time_collected")

            timestamp = parse_timestamp(timestamp_text, args.source_tz, timezone_map)
            row["id"] = coin_id
            row["time_collected"] = timestamp.strftime(UTC_FORMAT)

            previous = snapshots[timestamp].get(coin_id)
            if previous is not None and previous != row:
                raise ValueError(f"Dữ liệu xung đột cho {coin_id} tại {timestamp}")
            snapshots[timestamp][coin_id] = row

    if not snapshots:
        raise ValueError("CSV không có dữ liệu")
    if args.single_snapshot and len(snapshots) != 1:
        raise ValueError(f"Cần đúng một lượt thu thập, tìm thấy {len(snapshots)}")

    for timestamp, coins in sorted(snapshots.items()):
        folder = args.output_dir / f"collected_date={timestamp:%Y-%m-%d}"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"snapshot-{timestamp:%Y%m%dT%H%M%SZ}.csv"

        with path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=columns)
            writer.writeheader()
            for coin_id in sorted(coins):
                writer.writerow(coins[coin_id])

    output_rows = sum(len(coins) for coins in snapshots.values())
    print(f"Đọc {input_rows} dòng, xuất {output_rows} dòng, {len(snapshots)} snapshot")


if __name__ == "__main__":
    main()