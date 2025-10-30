prompt = "Please provide timestamped events from the video. When a diagram or model appears, also provide a detailed visual description of its components and layout, structured for a blind/low-vision user."

from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyCd2hteyh4L6d5fp4Rny-jwqlOdLrr7RRU")
response = client.models.generate_content(
    model='models/gemini-2.5-flash',
    contents=types.Content(
        parts=[
            types.Part(
                file_data=types.FileData(file_uri='https://youtu.be/LPZh9BOjkQs?si=i83fbT7R3oCUigNK'),
            ),
            types.Part(text=prompt)
        ]
    )
)
print(response.text)