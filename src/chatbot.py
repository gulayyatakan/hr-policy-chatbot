import ollama

MODEL_NAME = "phi3:mini"  # change this if you use another model
history = []  # keep chat history so the model has context


def main():
    print("Local LLm chat (Ollama). Type 'exit' or 'quit' to stop.\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Bot: Have a nice day!")
            break

        # 1) Add user message to history
        history.append({"role": "user", "content": user_input})

        # 2) Call Ollama chat
        response = ollama.chat(
            model=MODEL_NAME,
            messages=history,
        )

        # depending on the ollama client, response is a dict
        bot_text = response["message"]["content"]
        print(f"Bot: {bot_text}\n")

        # 3) Add bot answer to history
        history.append({"role": "assistant", "content": bot_text})


if __name__ == "__main__":
    main()