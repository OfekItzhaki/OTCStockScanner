import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_text(text, ticker=None):
    if not text.strip():
        return ""
    prompt = f"""
You are a financial analyst. Summarize the following news and state whether it may have a positive, negative, or neutral impact on the stock {ticker}. Also provide a KEEP/REMOVE suggestion.

News: {text}

Summary:
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # or gpt-4
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return ""
