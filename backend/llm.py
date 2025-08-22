import os
from groq import Groq

client =Groq(api_key=os.getenv("GROQ_API_KEY"))

def summarize_page(text: str) -> dict:
    prompt = f"""
    You are a documentation assistant.
    Summarize this content in human-readable format.
    Include Mermaid.js diagrams for architecture and any code snipppets.

    Content:
    {text}
    """
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
    )

    output = response.choices[0].message.content
    if " '''mermaid" in output:
        summary, diagram = output.split(" '''mermaid", 1)
        diagram = " '''mermaid" + diagram

    else:
        summary, diagram = output, ""
    return {"summary": summary.strip(), "diagram": diagram.strip()}

def chat_with_context(question: str, context: str) -> str:
    prompt = f"""
    Context from documentation:
    {context}

    Question:
    {question}
    """

    response = client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()
 