from sklearn.ensemble import IsolationForest

def detect_anomalies(df, feature_cols, contamination=0.05):
    X = df[feature_cols].fillna(0)
    
    model = IsolationForest(
        contamination=contamination,  # expect ~5% of logs to be anomalous
        random_state=42,              # reproducibility
        n_estimators=100              # number of isolation trees
    )
    
    df['anomaly_score'] = model.fit_predict(X)
    # fit_predict returns: -1 for anomalies, 1 for normal
    df['is_anomaly'] = df['anomaly_score'] == -1
    
    return df