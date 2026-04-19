import requests
import pandas as pd

session = requests.Session()

MODEL_NAME = "LiquidAI/LFM2.5-350M-GGUF:Q4_K_M"
URL = "http://127.0.0.1:8080/v1/chat/completions"

def classify_comment(comment):
    if not comment or not isinstance(comment, str):
        return "neutral"

    prompt = (
        "Classify the following YouTube comment into exactly one of these categories: "
        "affirmative, criticism, negative, neutral, question. "
        "Return only one word from that list.\n\n"
        f"Comment: {comment}"
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "You are a strict classifier. Reply with exactly one label only: affirmative, criticism, negative, neutral, or question."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0,
        "max_tokens": 5,
        "stream": False
    }

    valid_labels = {"affirmative", "criticism", "negative", "neutral", "question"}

    try:
        response = session.post(URL, json=payload, timeout=20)

        if response.status_code != 200:
            print("HTTP error:", response.status_code, response.text)
            return "neutral"

        result = response.json()
        prediction = result["choices"][0]["message"]["content"].strip().lower()

        # exact match first
        if prediction in valid_labels:
            return prediction

        # fallback cleanup
        for label in valid_labels:
            if label in prediction:
                return label

        return "neutral"

    except Exception as e:
        print("Request failed:", str(e))
        return "neutral"

def classify_comments(comments):
    df = pd.DataFrame(comments)
    if "text" not in df.columns:
        return df

    df["category"] = df["text"].astype(str).apply(classify_comment)
    return df