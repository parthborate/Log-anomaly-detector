import requests

def setup_llm():
    return "http://localhost:11434"

def explain_anomaly(base_url, log_lines_context):
    prompt = f"""You are a senior SRE. Below are log lines surrounding a detected anomaly.

LOG CONTEXT:
{log_lines_context}

Do three things:
1. Summarize the anomaly in 1-2 sentences.
2. Suggest the most probable root cause.
3. Suggest one specific diagnostic command an SRE would run next.

Be concise and practical."""

    response = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": "llama3.2:3b",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
    )
    return response.json()["message"]["content"]

def get_context_window(df, anomaly_index, window=10):
    start = max(0, anomaly_index - window)
    end = min(len(df), anomaly_index + window + 1)
    context_rows = df.iloc[start:end]

    lines = []
    for _, row in context_rows.iterrows():
        marker = ">>> ANOMALY >>>" if row.name == anomaly_index else "              "
        lines.append(f"{marker} {row['date']} {row['time']} {row['level']} {row['component']}: {row['message']}")

    return "\n".join(lines)