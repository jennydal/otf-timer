import os
import requests
from google import genai

# Route Reddit's RSS feed through a free public proxy to avoid GitHub Actions IP blocks
proxy_url = "https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Fwww.reddit.com%2Fr%2Forangetheory%2Fsearch.rss%3Fq%3Dtitle%3A%2522Daily%2BWorkout%2522%26sort%3Dnew%26restrict_sr%3Don"

# Fetch and parse the JSON response from the proxy
data = requests.get(proxy_url).json()

# The proxy stores the post body in the 'description' field of the first item
post_text = data['items'][0]['description']

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

# Call the generation endpoint (ensure the model is set to 2.5)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

# Clean the string output to ensure raw JSON
json_output = response.text.replace("```json", "").replace("```", "").strip()

# Save the payload locally
with open("today.seconds", "w") as f:
    f.write(json_output)

# Ping the Pushcut Webhook to alert your phone
pushcut_webhook = os.environ.get("PUSHCUT_WEBHOOK")
if pushcut_webhook:
    requests.post(pushcut_webhook)
