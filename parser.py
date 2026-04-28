import pandas as pd
import re

def parse_hdfs_logs(filepath):
    pattern = r'(\d{6})\s(\d{6})\s(\d+)\s(\w+)\s([\w\.\$]+):\s(.+)'
    records = []
    
    with open(filepath) as f:
        for line in f:
            match = re.match(pattern, line.strip())
            if match:
                records.append({
                    'date': match.group(1),
                    'time': match.group(2),
                    'pid': int(match.group(3)),
                    'level': match.group(4),
                    'component': match.group(5),
                    'message': match.group(6)
                })
    
    df = pd.DataFrame(records)
    return df