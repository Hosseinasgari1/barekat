import json, sys
sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('snapp_categories.json', 'r', encoding='utf-8'))
print(json.dumps(data[:30], ensure_ascii=False, indent=2))
print(f"\nTotal categories: {len(data)}")
