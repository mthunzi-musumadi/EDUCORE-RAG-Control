import re
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

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
# 2. VECTORSTORE
# ==========================================
vectorstore = Chroma.from_documents(
    documents=clean_documents,
    embedding=OllamaEmbeddings(model="nomic-embed-text")
)

# ==========================================
# 3. DETERMINISTIC ROUTING / RETRIEVAL
# ==========================================
def smart_retrieve(query: str) -> str:
    """
    If the query mentions a specific index (e.g., 'recipient 3' or 'to 1'),
    filter Chroma directly by metadata. Otherwise, fall back to vector search.
    """
    # Look for digits in user prompt
    match = re.search(r'\b(\d+)\b', query)
    
    if match:
        target_id = match.group(1)
        # Exact metadata match bypassing dense semantic vector noise
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
# 4. PROMPT & MODEL PIPELINE
# ==========================================
template = """You are a professional corporate email assistant.

Rules:
1. Locate the entry in the directory matching the requested index or name.
2. Address the email directly to that individual's name and reference their role.
3. Write a clear, professional email matching the user's prompt.
4. If no matching person is found in the directory, state: "Error: Recipient not found in the directory."

Directory:
{context}

User Prompt:
{question}

Email:
"""

prompt = ChatPromptTemplate.from_template(template)
llm = ChatOllama(model="llama3.2", temperature=0.1)

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

            # 1. Retrieve the exact matched document
            context = smart_retrieve(user_input)

            # 2. Invoke the chain directly
            chain = prompt | llm | StrOutputParser()
            response = chain.invoke({"context": context, "question": user_input})

            print("\n" + "-" * 40)
            print(response)
            print("-" * 40)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

if __name__ == "__main__":
    main()