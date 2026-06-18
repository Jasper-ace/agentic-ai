import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# ReAct Identity
react_identity = """
You are a Research Assistant. You have access to the following tools:

1. get_weather(city): Returns current temperature.
2. get_stock_price(symbol): Returns current stock price.

If you need a tool, respond ONLY with:
TOOL: [tool_name]([params])

Once you have the info, provide the final answer.
"""


def simulated_react_agent(user_query):
    print(f"\n[USER]: {user_query}")

    # Turn 1: Reasoning
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        config={"system_instruction": react_identity},
        contents=user_query
    )

    print(f"[AGENT]: {response.text}")

    # Turn 2: Action & Observation
    if "TOOL:" in response.text:
        tool_call = response.text.split("TOOL:")[1].strip()

        print(f"[ACTION] Agent requested tool: {tool_call}")

        # Simulated tool response
        observation = "OBSERVATION: The temperature in Manila is 32°C and sunny."

        print(f"[OBSERVE] Providing data: {observation}")

        # Turn 3: Final Answer
        final_response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            config={"system_instruction": react_identity},
            contents=[
                user_query,
                response.text,
                observation
            ]
        )

        print(f"\n[FINAL ANSWER]: {final_response.text}")

    else:
        print(f"\n[FINAL ANSWER]: {response.text}")


# Run the agent
simulated_react_agent("What should I wear in Manila today?")