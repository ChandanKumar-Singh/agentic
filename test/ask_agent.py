from ollama import Client

client = Client(host="http://192.168.1.13:11434")

while True:
    prompt = input("Ask something (or type exit): ")

    if prompt.lower() == "exit":
        break

    response = client.chat(
        model="deepseek-r1:1.5b",
        messages=[{"role": "user", "content": prompt}]
    )

    print("\nAI:", response["message"]["content"], "\n")

""" From terminal:
curl "http://YOUR_PC_IP:5000/ask?prompt=How does photosynthesis work?"

Example JSON response:
{
  "model": "deepseek-r1:1.5b",
  "prompt": "How does photosynthesis work?",
  "response": "Photosynthesis is the process where plants convert sunlight..."
} """