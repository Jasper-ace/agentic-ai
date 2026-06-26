from llama_index.core.node_parser import SentenceSplitter


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Splits text into overlapping chunks using LlamaIndex SentenceSplitter.

    Args:
        text (str): The raw text to split.
        chunk_size (int): Maximum number of tokens per chunk.
        chunk_overlap (int): Number of overlapping tokens between chunks.

    Returns:
        list[str]: A list of text chunks.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be less than chunk_size.")

    if not text or not text.strip():
        return []

    splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    return splitter.split_text(text)