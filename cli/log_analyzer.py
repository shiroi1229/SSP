# path: cli/log_analyzer.py
# version: v1

import os, json, argparse, datetime

LOG_DIR = os.getenv("SSP_LOG_DIR", "logs")

def list_logs():
    files = sorted(os.listdir(LOG_DIR), reverse=True)[:10]
    for f in files:
        print(f"📄 {f}")

def search_logs(keyword):
    for f in os.listdir(LOG_DIR):
        path = os.path.join(LOG_DIR, f)
        with open(path, encoding="utf-8") as file:
            content = file.read()
            try:
                parsed_content = json.loads(content)
                # JSONがリストの場合とオブジェクトの場合を考慮
                if isinstance(parsed_content, list):
                    for item in parsed_content:
                        # 各アイテムの文字列表現にキーワードが含まれるかチェック
                        if keyword in json.dumps(item, ensure_ascii=False):
                            print(f"🔍 {f}")
                            text_to_print = json.dumps(item.get("data", item), ensure_ascii=False, indent=2)
                            for line in text_to_print.splitlines():
                                print(f"  {line}")
                            print()
                            break # 最初のマッチで表示し、次のファイルへ
                else:
                    # オブジェクトの場合、その文字列表現にキーワードが含まれるかチェック
                    if keyword in content:
                        print(f"🔍 {f}")
                        text_to_print = json.dumps(parsed_content.get("data", parsed_content), ensure_ascii=False, indent=2)
                        for line in text_to_print.splitlines():
                            print(f"  {line}")
                        print()
            except (json.JSONDecodeError, UnicodeDecodeError):
                # JSON形式でないファイルはスキップ
                continue

def summarize_logs(count_only=False):
    count = 0
    dates = {}
    for f in os.listdir(LOG_DIR):
        path = os.path.join(LOG_DIR, f)
        with open(path, encoding="utf-8") as file:
            try:
                entry = json.load(file)
                if isinstance(entry, list):
                    for item in entry:
                        if "timestamp" in item:
                            date = item["timestamp"][:10]
                            dates[date] = dates.get(date, 0) + 1
                            count += 1
                else:
                    if "timestamp" in entry:
                        date = entry["timestamp"][:10]
                        dates[date] = dates.get(date, 0) + 1
                        count += 1
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue # JSON形式でないファイルはスキップ
    
    if count_only:
        print(count)
    else:
        print(f"📊 Total Logs: {count}")
        for d, c in sorted(dates.items()):
            print(f"  {d}: {c} entries")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSP Development Log Analyzer")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--search", type=str)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--count", action="store_true")
    args = parser.parse_args()

    if args.list:
        list_logs()
    elif args.search:
        search_logs(args.search)
    elif args.count:
        summarize_logs(count_only=True)
    elif args.summary:
        summarize_logs()
    else:
        parser.print_help()