import os
import requests
from google import genai

# Use a strictly compliant Reddit API User-Agent to bypass datacenter blocks
headers = {
    "User-Agent": "script:otf-timer-generator:v1.0 (by /u/gym-automation-bot)"
}
url = 'https://www.reddit.com/r/orangetheory/search.json?q=title:"Daily Workout"&sort=new&restrict_sr=on'

print("Fetching latest workout from Reddit...")
response = requests.get(url, headers=headers)

# Ensure we got a successful response before parsing
if response.status_code != 200:
    raise Exception(f"Reddit API refused the connection: {response.status_code} - {response.text}")

data = response.json()

# Safely extract the post body
try:
    post_text = data['data']['children'][0]['data']['selftext']
    print("Successfully retrieved workout text!")
except (KeyError, IndexError) as e:
    raise Exception(f"Unexpected JSON structure from Reddit. The post might not exist yet. Error: {e}")

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
