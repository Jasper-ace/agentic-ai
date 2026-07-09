import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def search_documents(query: str) -> str:
    """Search mock knowledge base."""
    return f"[Found] Context for {query}"

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What is chunking in RAG?",
    config=types.GenerateContentConfig(
        tools=[search_documents],
        temperature=0.0
    )
)

print("Text:", response.text)
print("Function Calls:", response.function_calls)
print("Candidates parts:", response.candidates[0].content.parts if response.candidates else None)
