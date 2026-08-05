import os
import requests
from google import genai

print("Fetching latest workout via PullPush API...")

# Use the PullPush submission endpoint to search for the specific phrase within the subreddit
url = 'https://api.pullpush.io/reddit/search/submission/?subreddit=orangetheory&q="Daily Workout"&sort=desc&size=1'

# Use a standard browser User-Agent
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

if response.status_code != 200:
    raise Exception(f"PullPush API failed: {response.status_code} - {response.text}")

data = response.json()

# Safely extract the post body from the PullPush payload
try:
    # PullPush returns an array of submissions in the 'data' key
    post_text = data['data'][0]['selftext']
    title = data['data'][0]['title']
    print(f"Successfully retrieved: {title}")
except (KeyError, IndexError) as e:
    raise Exception(f"Unexpected JSON structure from PullPush. The post might not exist yet. Error: {e}")

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
