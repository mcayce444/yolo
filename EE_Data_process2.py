import os
import shutil
import re  # For checking if folder contains 6-digit number
import fitz  # PyMuPDF
import logging
import hashlib
from difflib import SequenceMatcher
import sys

# Set up logging to overwrite the file each time the script is run
logging.basicConfig(filename='script_log.txt', level=logging.INFO,
                    format='%(asctime)s - %(message)s', filemode='w')  # 'w' mode overwrites the file

total_pages_deleted = 0
total_mb_deleted = 0
total_files_modified = 0

def get_folder_size(folder_path):
    """Helper function to calculate the size of a folder and its contents."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024)  # Return size in MB

def delete_specific_folders(base_folder, folders_to_delete):
    global total_mb_deleted, total_files_modified
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(base_folder):
        for folder in dirs:
            # Check if the folder is in the list of exact matches or starts with 'Intake'
            if folder in folders_to_delete or folder.startswith("Intake") or folder == "Photos" or folder == "Request":  # Adding "Request" folder to be deleted
                folder_path = os.path.join(root, folder)
                
                if os.path.exists(folder_path) and os.path.isdir(folder_path):
                    try:
                        # Calculate the folder size before deletion
                        folder_size = get_folder_size(folder_path)
                        # Delete the folder and all its contents
                        shutil.rmtree(folder_path)
                        total_mb_deleted += folder_size
                        total_files_modified += 1
                        logging.info(f"Deleted folder: {folder_path}, Size: {folder_size:.2f} MB")
                    except Exception as e:
                        logging.error(f"Error deleting {folder_path}: {e}")

def delete_files_with_keywords_and_extension(base_folder, keywords, extensions):
    global total_mb_deleted, total_files_modified
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            file_path = os.path.join(root, file)  # Ensure file_path is set for all cases
            
            # Check if the filename contains any of the keywords or matches the specified extensions
            if any(keyword in file for keyword in keywords) or any(file.endswith(ext) for ext in extensions) or "DRAFT" in file or "request" in file.lower():  # Added check for "DRAFT" and "request"
                try:
                    # Get the file size before deletion
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                    # Delete the file
                    os.remove(file_path)
                    total_mb_deleted += file_size
                    total_files_modified += 1
                    logging.info(f"Deleted file: {file_path}, Size: {file_size:.2f} MB")
                except Exception as e:
                    logging.error(f"Error deleting file {file_path}: {e}")

            # Rename "Police Report" to "TAR file"
            if "police report" in file.lower():  # Case-insensitive check for "Police Report"
                new_file_name = "TAR file" + os.path.splitext(file)[1]  # Keep the original file extension
                new_file_path = os.path.join(root, new_file_name)
                os.rename(file_path, new_file_path)
                logging.info(f"Renamed file: {file_path} to {new_file_path}")
                total_files_modified += 1



def check_and_rename_6_digit_folders(base_folder):
    global total_files_modified
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(base_folder):
        folder_name = os.path.basename(root)

        # Check if the folder name contains a 6-digit number and not "Azure"
        if re.search(r"\d{6}", folder_name) and "Azure" not in folder_name:
            found_closing_letter = False  # Flag to track if "Closing Letter" is found

            # Check if any file within the folder or its subfolders contains "Closing Letter" in the name
            for sub_root, sub_dirs, sub_files in os.walk(root):
                for file in sub_files:
                    # Use case-insensitive matching for "Closing Letter"
                    if re.search(r"closing\s*letter", file, re.IGNORECASE):
                        found_closing_letter = True  # Set flag to True
                        break

            # Rename folder if "Closing Letter" is found
            if found_closing_letter:
                new_folder_name = "Closed_" + folder_name
                new_folder_path = os.path.join(os.path.dirname(root), new_folder_name)
                
                try:
                    os.rename(root, new_folder_path)
                    total_files_modified += 1
                    logging.info(f"Renamed folder: {root} to {new_folder_path}")
                except Exception as e:
                    logging.error(f"Error renaming folder {root}: {e}")

def process_policy_pdfs(base_folder):
    global total_pages_deleted, total_mb_deleted, total_files_modified
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            # Check if the filename contains "Policy" and is a PDF
            if "Policy" in file and file.endswith(".pdf"):
                file_path = os.path.join(root, file)
                
                # Open the PDF
                try:
                    pdf_document = fitz.open(file_path)
                    num_pages = pdf_document.page_count
                    
                    # If the PDF has more than 10 pages, save only the first 10 pages
                    if num_pages > 10:
                        # Create new file path with "truncated_" prepended to the original filename
                        new_file_name = "truncated_" + file
                        new_file_path = os.path.join(root, new_file_name)
                        
                        # Get the original file size
                        original_file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                        
                        # Create a new PDF with only the first 10 pages
                        new_pdf = fitz.open()  # Create a new empty PDF
                        
                        for page_num in range(10):  # Copy the first 10 pages
                            new_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
                        
                        new_pdf.save(new_file_path)  # Save the new PDF with first 10 pages
                        new_pdf.close()
                        
                        # Get the new truncated file size
                        new_file_size = os.path.getsize(new_file_path) / (1024 * 1024)  # Size in MB
                        
                        # Calculate pages deleted and estimated size deleted
                        pages_deleted = num_pages - 10
                        size_deleted = original_file_size - new_file_size
                        
                        total_pages_deleted += pages_deleted
                        total_mb_deleted += size_deleted
                        
                        # Delete the original file
                        os.remove(file_path)
                        total_files_modified += 1
                        pdf_document.close()

                        logging.info(f"Processed and truncated PDF: {file_path}. Saved first 10 pages as {new_file_path}. Pages deleted: {pages_deleted}, MB deleted: {size_deleted:.2f} MB")
                    
                except Exception as e:
                       logging.error(f"Error processing PDF {file_path}: {e}")

def get_base_folder():
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
        print(folder_path)
        return folder_path
    else:
        print('no path provided')
        return 1

if __name__ == "__main__":
    # Base folder path
    #base_folder = r"C:\Users\MCayce\Documents\projects\scripts\testfolders"  # Replace with your actual base folder path
    # get base folder as cmd line arg
    base_folder = get_base_folder()

    # Subfolders to delete (add 'Liens', 'Costs', 'Photos', 'Requests', and any folder that starts with 'Intake')
    folders_to_delete = ["Liens", "Costs", "Photos", "Requests", "Invoices"]

    # Keywords to look for in filenames (e.g., 'LOR', 'UM Policy', 'DRAFT', 'request')
    file_keywords_to_delete = ["LOR", "UM Policy", "DRAFT", "request", "Reqs", "harmless", "Draft", "Reconciliation", "Reconcile", "Billing", "billing", "QBooks", "Req", "Check", "Pictures", "Policy Documents", "Investigation Report", "Rqst", "UIM Ltr of Rep"]

    # File extensions to delete
    file_extensions_to_delete = [".jpeg", ".mp4", ".mp3", ".png", ".jpg", "zip", "JPG", ".msg", ".xlsx"]  # Includes video, audio, and image files

    # Call the function to delete the specified folders
    delete_specific_folders(base_folder, folders_to_delete)

    # Call the function to delete files containing 'LOR', 'UM Policy', 'DRAFT', 'request', '.mp4', '.mp3', '.png', or any '.jpeg' files
    delete_files_with_keywords_and_extension(base_folder, file_keywords_to_delete, file_extensions_to_delete)

    # Call the function to check and rename folders with 6 digits if "Closing Letter" is found
    check_and_rename_6_digit_folders(base_folder)

    # Call the function to process PDFs with "Policy" in the name and more than 10 pages
    process_policy_pdfs(base_folder)

# After the script runs, print summary to terminal
    print(f"Total pages deleted from PDFs: {total_pages_deleted}")
    print(f"Estimated MB saved by truncating PDFs: {total_mb_deleted:.2f} MB")
    print(f"Total MB deleted (including files/folders): {total_mb_deleted:.2f} MB")
    print(f"Total number of files/folders modified: {total_files_modified}")

    # Log summary
    logging.info(f"Total pages deleted from PDFs: {total_pages_deleted}")
    logging.info(f"Estimated MB saved by truncating PDFs: {total_mb_deleted:.2f} MB")
    logging.info(f"Total MB deleted (including files/folders): {total_mb_deleted:.2f} MB")
    logging.info(f"Total number of files/folders modified: {total_files_modified}")
    


def calculate_file_hash(file_path, hash_algo=hashlib.md5):
    """Calculate and return the hash of the given file."""
    hash_obj = hash_algo()
    with open(file_path, 'rb') as f:
        # Read the file in chunks to avoid memory issues with large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()




 