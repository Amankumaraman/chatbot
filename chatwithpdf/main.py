#main.py

import re
from io import BytesIO
from typing import Tuple, List
from langchain.docstore.document import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from pypdf import PdfReader

def parse_pdf(file: BytesIO, filename: str) -> Tuple[List[str], str]:
    """
    Parse a PDF file and return a tuple containing a list of text pages and the filename.
    """
    pdf = PdfReader(file)
    output = []
    for page in pdf.pages:
        text = page.extract_text()
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
        text = re.sub(r"(?<!\n\s)\n(?!\s\n)", " ", text.strip())
        text = re.sub(r"\n\s*\n", "\n\n", text)
        output.append(text)
    return output, filename

def text_to_docs(pages: List[str], filename: str) -> List[Document]:
    """
    Convert a list of text pages into a list of Document objects with metadata.
    """
    page_docs = [Document(page_content=page) for page in pages]
    for i, doc in enumerate(page_docs):
        doc.metadata["page"] = i + 1

    doc_chunks = []
    for doc in page_docs:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            chunk_overlap=0,
        )
        chunks = text_splitter.split_text(doc.page_content)
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk, metadata={"page": doc.metadata["page"], "chunk": i}
            )
            doc.metadata["source"] = f"{doc.metadata['page']}-{doc.metadata['chunk']}"
            doc.metadata["filename"] = filename  # Add filename to metadata
            doc_chunks.append(doc)
    return doc_chunks

def docs_to_index(docs: List[Document], openai_api_key: str, existing_index=None) -> FAISS:
    """
    Create or update a vector index from a list of Document objects using OpenAI embeddings.
    """
    if existing_index:
        # Use the existing index and add new documents
        existing_index.add_documents(docs)
        return existing_index
    else:
        # Create a new index and add documents
        index = FAISS.from_documents(docs, OpenAIEmbeddings(openai_api_key=openai_api_key))
        return index

def get_index_for_pdf(pdf_files: List[BytesIO], pdf_names: List[str], openai_api_key: str, existing_index=None) -> FAISS:
    """
    Process multiple PDF files and return a vector index.
    """
    documents = []
    for pdf_file, pdf_name in zip(pdf_files, pdf_names):
        text, filename = parse_pdf(pdf_file, pdf_name)
        documents += text_to_docs(text, filename)
    index = docs_to_index(documents, openai_api_key, existing_index)
    return index