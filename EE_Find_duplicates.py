from difflib import SequenceMatcher
from datasketch import MinHash, MinHashLSH
import fitz  # PyMuPDF for PDF extraction
from docx import Document
import os
import re
import sys

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    text = []
    try:
        with fitz.open(pdf_path) as pdf_doc:
            for page in pdf_doc:
                text.append(page.get_text("text"))
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return "\n".join(text)

def extract_text_from_docx(docx_path):
    """Extracts text from a DOCX file."""
    doc = Document(docx_path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)

def get_text_from_file(file_path):
    """Extracts text from a file based on its extension."""
    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        return extract_text_from_docx(file_path)
    else:
        return None

def get_shingles(text, k=5):
    """Creates shingles of size k from text."""
    words = re.findall(r'\w+', text.lower())
    return [tuple(words[i:i+k]) for i in range(len(words) - k + 1)]

def create_minhash(shingles, num_perm=128):
    """Creates a MinHash object from shingles."""
    m = MinHash(num_perm=num_perm)
    for shingle in shingles:
        m.update(" ".join(shingle).encode('utf8'))
    return m

def find_near_duplicates(base_folder, content_similarity_threshold=0.95, filename_similarity_threshold=0.85):
    """Finds near-duplicate documents within a folder and subfolders."""
    lsh = MinHashLSH(threshold=content_similarity_threshold, num_perm=128)
    file_text_map = {}
    minhash_map = {}

    # Traverse all files in the folder and its subfolders
    for root, _, files in os.walk(base_folder):
        for file in files:
            # Skip hidden or temporary files (those starting with '~$' or '.')
            if file.startswith('~$') or file.startswith('.'):
                print(f"Skipping temporary or hidden file: {file}")
                continue

            file_path = os.path.join(root, file)
            if file_path.lower().endswith(('.pdf', '.docx')):
                text = get_text_from_file(file_path)
                if text:
                    file_text_map[file_path] = text
                    shingles = get_shingles(text)
                    minhash = create_minhash(shingles)
                    minhash_map[file_path] = minhash
                    lsh.insert(file_path, minhash)

    # Finding near-duplicates
    near_duplicates = []
    for file_path, minhash in minhash_map.items():
        similar_files = lsh.query(minhash)
        for similar_file in similar_files:
            if file_path != similar_file:
                # Check filename similarity
                filename_similarity = SequenceMatcher(None, os.path.basename(file_path), os.path.basename(similar_file)).ratio()
                
                # Only consider near-duplicates if both content and filename similarities meet the thresholds
                if filename_similarity >= filename_similarity_threshold:
                    near_duplicates.append((file_path, similar_file))

    # Prompt user to delete older duplicates
    reported_pairs = set()
    for file1, file2 in near_duplicates:
        # Avoid reporting the same pair twice
        if (file2, file1) not in reported_pairs:
            file1_name = os.path.basename(file1)
            file2_name = os.path.basename(file2)

            # Check if both files still exist before getting modification time
            if not os.path.exists(file1) or not os.path.exists(file2):
                print(f"One of the files '{file1}' or '{file2}' no longer exists. Skipping this pair.")
                continue  # Skip this pair if one of the files was already deleted

            # Re-check file existence just before accessing modification time
            if os.path.exists(file1) and os.path.exists(file2):
                # Determine which file is older based on modification time
                file1_mtime = os.path.getmtime(file1)
                file2_mtime = os.path.getmtime(file2)

                if file1_mtime > file2_mtime:
                    # file1 is more recent
                    older_file, recent_file = file2, file1
                else:
                    # file2 is more recent
                    older_file, recent_file = file1, file2

                # Prompt user to delete the older file
                print(f"\nDuplicate files found:\n  1. {file1_name} (older)\n  2. {file2_name} (recent)")
                choice = input(f"Do you want to delete the older file '{os.path.basename(older_file)}'? (y/n): ")

                if choice.lower() == 'y':
                    if os.path.exists(older_file):  # Final check before deletion
                        try:
                            os.remove(older_file)
                            print(f"Deleted: {os.path.basename(older_file)}")
                        except Exception as e:
                            print(f"Error deleting {older_file}: {e}")
                    else:
                        print(f"The file '{older_file}' was already deleted or moved.")
                else:
                    print("Skipped deletion.")

                # Mark this pair as processed
                reported_pairs.add((file1, file2))

# Example usage
#base_folder = r"C:\Users\MCayce\Documents\projects\scripts\testfolders"  # Replace with your actual base folder path

def get_base_folder():
    # get base folder path as cmd line arg
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
        print(folder_path)
        return folder_path
    else:
        print('no path provided')
        return 1

if __name__ == "__main__":
    base_folder = get_base_folder()
    find_near_duplicates(base_folder)
