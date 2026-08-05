import os
import requests
import urllib.parse
from google import genai

print("Fetching latest workout via AllOrigins proxy...")

# The target Reddit URL (URL-encoded to pass safely through the proxy)
reddit_url = 'https://www.reddit.com/r/orangetheory/search.json?q=title:"Daily Workout"&sort=new&restrict_sr=on'
encoded_url = urllib.parse.quote(reddit_url, safe='')

# Route through AllOrigins to bypass Reddit's IP block on GitHub Actions
proxy_url = f"https://api.allorigins.win/raw?url={encoded_url}"

# Use a standard browser User-Agent
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(proxy_url, headers=headers)

if response.status_code != 200:
    raise Exception(f"Proxy failed: {response.status_code} - {response.text}")

data = response.json()

# Safely extract the post body
try:
    post_text = data['data']['children'][0]['data']['selftext']
    print("Successfully retrieved workout text!")
except (KeyError, IndexError) as e:
    raise Exception(f"Unexpected JSON structure. Error: {e}")

# Initialize the Gemini client
client = genai.Client()

prompt = f"""
Parse this Orangetheory workout into valid Seconds Timer JSON format (.seconds).
Use type: 0, a top-level "items" array, and assign color 2 for Push, 1 for All Out, 4 for Base/Warmup.
Embed exercise rep lists into the interval names.
Return ONLY valid JSON without Markdown formatting blocks or extra text.

Workout Text:
{post_text}
"""

print("Generating timer JSON via Gemini...")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

# Clean the string output to ensure raw JSON
json_output = response.text.replace("```json", "").replace("```", "").strip()

# Save the payload locally
with open("today.seconds", "w") as f:
    f.write(json_output)
print("Saved today.seconds locally.")

# Ping the Pushcut Webhook to alert your phone
pushcut_webhook = os.environ.get("PUSHCUT_WEBHOOK")
if pushcut_webhook:
    print("Pinging iOS Pushcut webhook...")
    requests.post(pushcut_webhook)
    print("Webhook sent!")
