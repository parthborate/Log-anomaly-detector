from parser import parse_hdfs_logs

df = parse_hdfs_logs('data/HDFS_2k.log')
print(df.head())
print(df['level'].value_counts())