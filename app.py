import os
import re
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Ensure Ollama client environment defaults allow co-residence
os.environ.setdefault("OLLAMA_MAX_LOADED_MODELS", "2")
os.environ.setdefault("OLLAMA_KEEP_ALIVE", "-1")

# ==========================================
# 1. INGESTION WITH METADATA TAGGING
# ==========================================
SENSITIVE_FIELD_REGEX = re.compile(
    r'\|\s*(Phone|Address|Mobile|Tel|Residence|National ID):\s*[^|\n]+',
    re.IGNORECASE
)
INDEX_EXTRACTOR = re.compile(r'^\[(\d+)\]')

def load_and_sanitize_directory(file_path: str) -> list[Document]:
    sanitized_docs = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # 1. Extract the index number for metadata filtering
            index_match = INDEX_EXTRACTOR.match(line)
            record_id = index_match.group(1) if index_match else "unknown"

            # 2. Strip sensitive PII
            cleaned_line = SENSITIVE_FIELD_REGEX.sub('', line).strip()
            cleaned_line = re.sub(r'\|\s*$', '', cleaned_line).strip()

            # 3. Store clean text with explicit metadata
            sanitized_docs.append(
                Document(
                    page_content=cleaned_line,
                    metadata={"index": record_id}
                )
            )
            
    return sanitized_docs

clean_documents = load_and_sanitize_directory("data.txt")

# ==========================================
# 2. VECTORSTORE (EMBEDDING PINNED IN MEMORY)
# ==========================================
# keep_alive=-1 pins nomic-embed-text indefinitely in RAM to prevent model swapping
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    keep_alive=-1
)
vectorstore = Chroma.from_documents(
    documents=clean_documents,
    embedding=embeddings
)

# ==========================================
# 3. DETERMINISTIC ROUTING / RETRIEVAL
# ==========================================
def smart_retrieve(query: str) -> str:
    """
    If the query mentions a specific index (e.g., 'recipient 3' or 'to 1'),
    fetch directly from Chroma metadata bypassing embedding calls.
    Otherwise, fall back to vector search.
    """
    # Look for digits in user prompt
    match = re.search(r'\b(\d+)\b', query)
    
    if match:
        target_id = match.group(1)
        # 1. Zero-latency exact metadata fetch directly from SQLite (bypasses embedding model)
        docs = vectorstore.get(where={"index": target_id})
        if docs and docs.get("documents"):
            return docs["documents"][0]

        # 2. Filtered vector search fallback
        results = vectorstore.similarity_search(
            query,
            k=1,
            filter={"index": target_id}
        )
        if results:
            return results[0].page_content

    # Fallback: retrieve top 4 if no explicit ID was requested
    fallback_results = vectorstore.similarity_search(query, k=4)
    return "\n".join(doc.page_content for doc in fallback_results)

# ==========================================
# 4. PROMPT & MODEL PIPELINE (HARDWARE TUNED)
# ==========================================
# Separate System Message allows Ollama to cache system prompt KV tokens across turns
prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a professional corporate email assistant.\n\n"
        "Rules:\n"
        "1. Locate the entry in the directory matching the requested index or name.\n"
        "2. Address the email directly to that individual's name and reference their role.\n"
        "3. Write a clear, concise, professional email matching the user's prompt.\n"
        "4. If no matching person is found in the directory, state: \"Error: Recipient not found in the directory.\""
    )),
    ("human", "Directory:\n{context}\n\nUser Request:\n{question}\n\nEmail:")
])

# Hardware-tuned runtime parameters matching native Ollama efficiency
llm = ChatOllama(
    model="llama3.2",
    temperature=0.1,
    num_thread=4,         # Match physical cores: eliminates SMT hyperthread cache thrashing
    num_ctx=2048,         # Keeps KV cache compact within CPU L3 cache
    num_predict=256,      # Maximum response horizon; avoids runaway token loops on CPU
    top_k=40,
    top_p=0.9,
    repeat_penalty=1.15,
    keep_alive=-1         # Pinned indefinitely in RAM alongside nomic-embed-text
)

# Reusable LCEL pipeline (instantiated once outside the interaction loop)
chain = prompt | llm | StrOutputParser()

# Pre-warm both models so initial prompt response is instant with zero cold-start delay
try:
    embeddings.embed_query("warmup")
    llm.invoke("warmup")
except Exception:
    pass

# ==========================================
# 5. INTERACTIVE LOOP
# ==========================================
def main():
    print("=" * 65)
    print("Email Generator [Deterministic Metadata Routing Enabled]")
    print("Try: 'Draft an email to recipient 1'")
    print("Try: 'Write a memo to 4'")
    print("Type 'exit' to quit.")
    print("=" * 65)

    while True:
        try:
            user_input = input("\nRequest > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                break

            # 1. Retrieve the exact matched document (zero-overhead metadata lookup)
            context = smart_retrieve(user_input)

            # 2. Stream tokens directly to the app
            print("\n" + "-" * 40)
            for chunk in chain.stream({"context": context, "question": user_input}):
                print(chunk, end="", flush=True)
            print("\n" + "-" * 40)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

if __name__ == "__main__":
    main()