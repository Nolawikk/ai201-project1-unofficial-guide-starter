import os
from groq import Groq
from dotenv import load_dotenv
from embed import retrieve

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

# ── Grounded generation ───────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a helpful assistant for UCLA transfer students.
You answer questions using ONLY the provided document excerpts.
Do not use any outside knowledge or make anything up.
If the provided documents do not contain enough information to answer the question, say exactly:
"I don't have enough information in my documents to answer that."

Always end your answer with a "Sources:" section listing the document names you drew from.
Format sources as a bullet list."""


def ask(question: str) -> dict:
    """Retrieve relevant chunks and generate a grounded answer."""
    chunks = retrieve(question)

    # Build context from retrieved chunks
    context = ""
    for i, chunk in enumerate(chunks):
        context += f"[Document {i+1}: {chunk['source']}]\n{chunk['text']}\n\n"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Documents:\n{context}\n\nQuestion: {question}"}
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=1000
    )

    answer = response.choices[0].message.content
    sources = list(set(chunk["source"] for chunk in chunks))

    return {
        "answer": answer,
        "sources": sources,
        "chunks": chunks
    }


# ── Gradio interface ──────────────────────────────────────────────────────────
import gradio as gr

def handle_query(question: str):
    if not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    sources_text = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources_text


with gr.Blocks(title="UCLA Transfer Student Unofficial Guide") as demo:
    gr.Markdown("# 🐻 UCLA Transfer Student Unofficial Guide")
    gr.Markdown("Ask anything about transferring to UCLA — housing, dining, enrollment, and more.")

    with gr.Row():
        inp = gr.Textbox(
            label="Your question",
            placeholder="e.g. What is the housing lottery process for transfer students?",
            lines=2
        )

    btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        answer = gr.Textbox(label="Answer", lines=10)
        sources = gr.Textbox(label="Retrieved from", lines=10)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

    gr.Markdown("### Example questions")
    gr.Examples(
        examples=[
            "What is the housing lottery process for transfer students?",
            "Which dining hall do students recommend most at UCLA?",
            "What do students say about enrollment appointments for transfers?",
            "What mental health resources exist for transfer students?",
            "What are common mistakes transfer students make in their first quarter?",
        ],
        inputs=inp
    )


if __name__ == "__main__":
    # Quick test before launching UI
    print("Testing grounded generation...")
    test = ask("What is the housing lottery process for transfer students?")
    print("\nAnswer:", test["answer"][:500])
    print("\nSources:", test["sources"])

    print("\n\nLaunching Gradio interface...")
    demo.launch()
