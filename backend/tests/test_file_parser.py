"""
Test script for the FileParser functionality
"""
import asyncio
import tempfile
import os
from fastapi import UploadFile
from file_parser import FileParser

async def test_file_parser():
    """Test the FileParser with different file types"""
    
    # Create a test text file
    test_content = """
    This is a test document for the file parser.
    
    It contains multiple paragraphs to test the chunking functionality.
    
    The parser should be able to handle various file types including:
    - Text files (.txt)
    - PDF files (.pdf) 
    - Word documents (.docx)
    - Markdown files (.md)
    - HTML files (.html)
    - CSV files (.csv)
    - JSON files (.json)
    
    Each file type should be parsed appropriately and split into chunks.
    """
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write(test_content)
        temp_file_path = temp_file.name
    
    try:
        # Create a mock UploadFile
        with open(temp_file_path, 'rb') as f:
            file_content = f.read()
        
        # Create UploadFile mock
        upload_file = UploadFile(
            filename="test_document.txt",
            file=open(temp_file_path, 'rb'),
            content_type="text/plain"
        )
        
        # Test the parser
        parser = FileParser(chunk_size=200, chunk_overlap=50)
        documents = await parser.parse_uploaded_file(upload_file)
        
        print(f"Successfully parsed file into {len(documents)} chunks")
        for i, doc in enumerate(documents):
            print(f"Chunk {i+1}: {doc.page_content[:100]}...")
            print(f"Metadata: {doc.metadata}")
            print("-" * 50)
        
        # Test supported file types
        supported_types = parser.get_supported_file_types()
        print(f"Supported file types: {supported_types}")
        
    except Exception as e:
        print(f"Error testing file parser: {e}")
    
    finally:
        # Clean up
        try:
            os.unlink(temp_file_path)
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_file_parser())
