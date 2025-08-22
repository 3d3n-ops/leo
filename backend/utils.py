from typing import List

def chunk_lines(lines: List[str], chunk_size: int = 500) -> List[str]:
    """
    Split lines into chunks of specified size (by character count)
    """
    chunks = []
    current_chunk = ""
    current_size = 0
    
    for line in lines:
        line_length = len(line) + 1  # +1 for newline
        
        # If adding this line would exceed chunk size, start new chunk
        if current_size + line_length > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = line
            current_size = line_length
        else:
            if current_chunk:
                current_chunk += "\n" + line
            else:
                current_chunk = line
            current_size += line_length
    
    # Add the last chunk if it exists
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks