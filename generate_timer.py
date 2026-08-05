import os
import requests
from google import genai

# Fetch the latest Daily Workout text from Reddit
url = 'https://www.reddit.com/r/orangetheory/search.json?q=title:"Daily Workout"&sort=new&restrict_sr=on'
headers = {"User-Agent": "OTF-Timer-Bot/1.0"}
data = requests.get(url, headers=headers).json()
post_text = data['data']['children'][0]['data']['selftext']

# Initialize the Gemini client (automatically uses the GEMINI_API_KEY environment variable)
client = genai.Client()

prompt = f"""
Parse this Orangetheory workout into valid Seconds Timer JSON format (.seconds).
Use type: 0, a top-level "items" array, and assign color 2 for Push, 1 for All Out, 4 for Base/Warmup.
Embed exercise rep lists into the interval names.
Return ONLY valid JSON without Markdown formatting blocks or extra text.

Workout Text:
{post_text}
"""

# Call the generation endpoint
response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents=prompt
)

# Clean the string output to ensure raw JSON
json_output = response.text.replace("```json", "").replace("```", "").strip()

# Save the payload locally for GitHub Actions to commit
with open("today.seconds", "w") as f:
    f.write(json_output)

# Ping the Pushcut Webhook to alert your phone
pushcut_webhook = os.environ.get("PUSHCUT_WEBHOOK")
if pushcut_webhook:
    requests.post(pushcut_webhook)
