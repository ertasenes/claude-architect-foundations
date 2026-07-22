import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    messages=[
        {"role": "user", "content": "Hello Claude! Explain in one sentence what an API is."}
    ]
)

print(response.content[0].text)
