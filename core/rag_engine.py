import os
from langchain_mistralai import ChatMistralAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from core.vector_store import build_vector_store, load_vector_store, get_retriever


PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert meeting assistant. Answer the user's question
based ONLY on the meeting transcript context provided below.

If the answer is not found in the context, say:
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly.

Context from meeting transcript:
{context}""",
    ),
    ("human", "{question}"),
])


def get_llm():
    return ChatGroq(
        model="qwen/qwen3.8-27b", 
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3,
    )


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def _build_chain(vector_store):
    retriever = get_retriever(vector_store, k=4)
    return (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | PROMPT
        | get_llm()
        | StrOutputParser()
    )


def build_rag_chain(transcript: str):
    return _build_chain(build_vector_store(transcript))


def load_rag_chain():
    return _build_chain(load_vector_store())


def ask_question(rag_chain, question: str) -> str:
    print(f"Question: {question}")
    answer = rag_chain.invoke(question)
    print(f"Answer: {answer}")
    return answer