# RAG Documents Source Folder

This folder serves as the central repository for all raw text data files (`.txt`) used by the Retrieval-Augmented Generation (RAG) system.

## How to use:
1. **Upload Data:** Place all your raw `.txt` files containing information about schemes, agricultural guidelines, or any other relevant data directly into this folder.
2. **Chunking and Extraction:** Your RAG processing scripts should be configured to read from this directory (`app/data/rag_documents`), parse each `.txt` file, extract the meaning chunks, and compile the necessary metadata (e.g., region, crop_type, land_size_eligibility) required by your `SchemeRanker` to enhance search accuracy.

## Data Convention Tips:
- **Consistent Naming:** Try to name your files descriptively (e.g., `maharashtra_cotton_subsidies.txt`).
- **Metadata Structure:** If you plan on extracting metadata easily, consider adding a standard header block at the top of each `.txt` file, for instance:
  ```yaml
  Region: Maharashtra
  Crop: Cotton
  Eligibility: Small Farmer (< 5 acres)
  ```
  This will make writing your chunking and metadata extraction scripts much simpler!
