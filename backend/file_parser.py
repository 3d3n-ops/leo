import os
import tempfile
import logging
from typing import List, Optional
from fastapi import UploadFile
import magic
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
    CSVLoader,
    JSONLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class FileParser:
    """Parser for various file types using LangChain document loaders"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type of the file"""
        try:
            mime = magic.Magic(mime=True)
            return mime.from_file(file_path)
        except Exception as e:
            logger.warning(f"Could not determine MIME type for {file_path}: {e}")
            return "application/octet-stream"
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename"""
        return os.path.splitext(filename)[1].lower()
    
    def _select_loader(self, file_path: str, mime_type: str, filename: str):
        """Select appropriate LangChain loader based on file type"""
        file_ext = self._get_file_extension(filename)
        
        # MIME type based selection
        if mime_type == "text/plain":
            return TextLoader(file_path, encoding="utf-8")
        elif mime_type == "application/pdf":
            return PyPDFLoader(file_path)
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return UnstructuredWordDocumentLoader(file_path)
        elif mime_type == "text/markdown":
            return UnstructuredMarkdownLoader(file_path)
        elif mime_type == "text/html":
            return UnstructuredHTMLLoader(file_path)
        elif mime_type == "text/csv":
            return CSVLoader(file_path)
        elif mime_type == "application/json":
            return JSONLoader(file_path)
        
        # Fallback to file extension
        elif file_ext == ".txt":
            return TextLoader(file_path, encoding="utf-8")
        elif file_ext == ".pdf":
            return PyPDFLoader(file_path)
        elif file_ext in [".docx", ".doc"]:
            return UnstructuredWordDocumentLoader(file_path)
        elif file_ext == ".md":
            return UnstructuredMarkdownLoader(file_path)
        elif file_ext in [".html", ".htm"]:
            return UnstructuredHTMLLoader(file_path)
        elif file_ext == ".csv":
            return CSVLoader(file_path)
        elif file_ext == ".json":
            return JSONLoader(file_path)
        
        # Default to text loader for unknown types
        else:
            logger.warning(f"Unknown file type {mime_type} ({file_ext}), attempting to parse as text")
            return TextLoader(file_path, encoding="utf-8")
    
    async def parse_uploaded_file(self, file: UploadFile) -> List[Document]:
        """
        Parse uploaded file and return document chunks
        """
        logger.info(f"Parsing uploaded file: {file.filename} (type: {file.content_type})")
        
        # Create temporary file to store uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Determine MIME type
            mime_type = self._get_mime_type(temp_file_path)
            logger.info(f"Detected MIME type: {mime_type}")
            
            # Select appropriate loader
            loader = self._select_loader(temp_file_path, mime_type, file.filename)
            
            # Load documents
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} documents from {file.filename}")
            
            # Add metadata to documents
            for doc in documents:
                doc.metadata.update({
                    "source": file.filename,
                    "file_type": mime_type,
                    "original_filename": file.filename
                })
            
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Created {len(chunks)} chunks from {file.filename}")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error parsing file {file.filename}: {e}")
            # Fallback: try to read as plain text
            try:
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                
                doc = Document(
                    page_content=text_content,
                    metadata={
                        "source": file.filename,
                        "file_type": "text/plain",
                        "original_filename": file.filename,
                        "parsing_method": "fallback_text"
                    }
                )
                
                chunks = self.text_splitter.split_documents([doc])
                logger.info(f"Fallback parsing created {len(chunks)} chunks from {file.filename}")
                return chunks
                
            except Exception as fallback_error:
                logger.error(f"Fallback parsing also failed for {file.filename}: {fallback_error}")
                return []
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Could not delete temporary file {temp_file_path}: {e}")
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types"""
        return [
            "text/plain",
            "application/pdf", 
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/markdown",
            "text/html",
            "text/csv",
            "application/json",
            ".txt", ".pdf", ".docx", ".doc", ".md", ".html", ".htm", ".csv", ".json"
        ]
