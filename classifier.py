from textblob import TextBlob
import pandas as pd

def classify_comment(comment):
    text = comment.lower()
    if '?' in text:
        return 'question'
    elif any(word in text for word in ['bad', 'worst', 'hate', 'not good', 'terrible', 'disagree']):
        return 'criticism'
    elif any(word in text for word in ['good', 'love', 'nice', 'amazing', 'agree', 'great', 'awesome']):
        return 'affirmative'
    else:
        polarity = TextBlob(comment).sentiment.polarity
        if polarity > 0.2:
            return 'affirmative'
        elif polarity < -0.2:
            return 'criticism'
        else:
            return 'neutral'

def classify_comments(comments):
    df = pd.DataFrame(comments)
    df["category"] = df["text"].astype(str).apply(classify_comment)
    return df
