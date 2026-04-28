def engineer_features(df):
    # Feature 1: Is this an error-level log?  (1 = ERROR, 0 = otherwise)
    df['is_error'] = (df['level'] == 'ERROR').astype(int)
    
    # Feature 2: Message length (unusually long messages often signal stack traces)
    df['msg_length'] = df['message'].str.len()
    
    # Feature 3: How common is this component? Rare components are more suspicious
    comp_counts = df['component'].value_counts()
    df['component_frequency'] = df['component'].map(comp_counts)
    
    # Feature 4: PID — unusual PIDs can indicate rogue processes
    df['pid_normalized'] = (df['pid'] - df['pid'].mean()) / df['pid'].std()
    
    feature_cols = ['is_error', 'msg_length', 'component_frequency', 'pid_normalized']
    return df, feature_cols