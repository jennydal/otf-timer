import os
import requests
from google import genai

print("Fetching latest workout post via PullPush API...")

# STEP 1: Get the Daily Workout Submission
url = 'https://api.pullpush.io/reddit/search/submission/?subreddit=orangetheory&q="Daily Workout"&sort=desc&size=1'
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

if response.status_code != 200:
    raise Exception(f"PullPush Submission API failed: {response.status_code}")

data = response.json()

try:
    # Extract the unique Reddit name ID (e.g., t3_1kq3kqy)
    submission_name = data['data'][0]['name']
    title = data['data'][0]['title']
    print(f"Found post: {title}")
except (KeyError, IndexError) as e:
    raise Exception(f"Unexpected JSON structure. Post might not exist yet. Error: {e}")

# STEP 2: Fetch the comments for that specific submission
print("Fetching comments to find the workout intel...")
comment_url = f"https://api.pullpush.io/reddit/search/comment/?link_id={submission_name}"
comment_response = requests.get(comment_url, headers=headers)

if comment_response.status_code != 200:
    raise Exception(f"PullPush Comment API failed: {comment_response.status_code}")

comment_data = comment_response.json()
comments = comment_data.get('data', [])

if not comments:
    raise Exception("No comments found on this post yet. Intel hasn't been posted.")

# The actual workout intel is typically the longest comment on the thread. 
# We sort comments by the length of their body text and grab the largest one.
workout_comment = max(comments, key=lambda c: len(c.get('body', '')))
post_text = workout_comment.get('body', '')

print(f"Extracted workout intel (Length: {len(post_text)} characters).")

# STEP 3: Initialize the Gemini client and generate JSON
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
