import json
from pathlib import Path

# Load both files
file1_path = Path('../timesheet_webapp_data.json')
file2_path = Path('../timesheet_webapp_data_2.json')

with open(file1_path, 'r', encoding='utf-8') as f:
    data1 = json.load(f)

with open(file2_path, 'r', encoding='utf-8') as f:
    data2 = json.load(f)

# Compare basic structure
print('🔍 Comparing JSON files...')
print(f'File 1: {len(data1)} top-level keys')
print(f'File 2: {len(data2)} top-level keys')

# Check if keys match
keys1 = set(data1.keys())
keys2 = set(data2.keys())

if keys1 == keys2:
    print('✅ Top-level keys match')
else:
    print('❌ Top-level keys differ')
    print(f'Only in file 1: {keys1 - keys2}')
    print(f'Only in file 2: {keys2 - keys1}')

# Compare key sections
sections_to_compare = [
    'company', 'employee', 'period', 'daily_timesheet_summary',
    'compliance_summary', 'period_totals'
]

differences = []

for section in sections_to_compare:
    if section in data1 and section in data2:
        if data1[section] != data2[section]:
            differences.append(section)
            print(f'❌ Section "{section}" differs')
        else:
            print(f'✅ Section "{section}" matches')
    else:
        print(f'⚠️ Section "{section}" missing in one file')

# Check timesheet data count
if 'timesheet_data' in data1 and 'timesheet_data' in data2:
    count1 = len(data1['timesheet_data'])
    count2 = len(data2['timesheet_data'])
    if count1 == count2:
        print(f'✅ Timesheet data count matches: {count1} records')
    else:
        print(f'❌ Timesheet data count differs: {count1} vs {count2}')

# Check metadata differences (expected to be different)
if 'metadata' in data1 and 'metadata' in data2:
    meta1 = data1['metadata']
    meta2 = data2['metadata']
    
    print('📊 Metadata comparison:')
    for key in ['export_timestamp', 'data_source', 'total_records_processed']:
        if key in meta1 and key in meta2:
            if meta1[key] != meta2[key]:
                print(f'  {key}: "{meta1[key]}" vs "{meta2[key]}"')
            else:
                print(f'  {key}: matches')

print(f'\n📋 Summary: {len(differences)} sections differ (excluding metadata)')
if len(differences) == 0:
    print('🎉 Files are essentially identical!')
else:
    print(f'⚠️ Differences found in: {differences}')
    
    # Show specific differences
    for section in differences:
        print(f'\n🔍 Differences in "{section}":')
        if isinstance(data1[section], dict) and isinstance(data2[section], dict):
            for key in data1[section]:
                if key not in data2[section]:
                    print(f'  Key "{key}" only in file 1')
                elif data1[section][key] != data2[section][key]:
                    print(f'  Key "{key}": "{data1[section][key]}" vs "{data2[section][key]}"')
            for key in data2[section]:
                if key not in data1[section]:
                    print(f'  Key "{key}" only in file 2')
        else:
            print(f'  File 1: {data1[section]}')
            print(f'  File 2: {data2[section]}')