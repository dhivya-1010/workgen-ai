import ollama

def ai_agent(user_input):

    response = ollama.chat(
        model="tinyllama",
        messages=[
            {"role": "user", "content": user_input}
        ]
    )

    return response["message"]["content"]


while True:
    user = input("You: ")
    print("AI:", ai_agent(user))