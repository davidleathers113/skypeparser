"""
File handling utilities for the Skype Parser project.

This module provides functions for reading and extracting data from various file formats,
including JSON files and TAR archives. It's designed to work with uploaded files in
web applications or other automated processing systems.

This module serves as the foundation for the Extraction phase of the ETL pipeline,
providing robust functionality for extracting data from Skype export archives.
"""

import os
import json
import tarfile
import re
import logging
import tempfile
from typing import Dict, List, Union, Optional, Tuple, Any, BinaryIO

# Set up logging
logger = logging.getLogger(__name__)

def read_file(filename: str) -> Dict[str, Any]:
    """
    Read and parse a JSON file.

    Args:
        filename (str): Path to the JSON file

    Returns:
        dict: Parsed JSON data

    Raises:
        json.JSONDecodeError: If the file is not valid JSON
        FileNotFoundError: If the file does not exist
    """
    try:
        with open(filename, encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}")
        raise

def read_file_object(file_obj: BinaryIO) -> Dict[str, Any]:
    """
    Read and parse a JSON file from a file-like object.
    This is useful for processing uploaded files without saving them to disk.

    Args:
        file_obj (BinaryIO): File-like object containing JSON data

    Returns:
        dict: Parsed JSON data

    Raises:
        json.JSONDecodeError: If the content is not valid JSON
    """
    try:
        # Reset file pointer to beginning
        file_obj.seek(0)
        content = file_obj.read()

        # If content is bytes, decode to string
        if isinstance(content, bytes):
            content = content.decode('utf-8')

        data = json.loads(content)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON content: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading file object: {e}")
        raise

def read_tarfile(filename: str, select_json: Optional[int] = None,
                 auto_select: bool = True) -> Dict[str, Any]:
    """
    Extract and read a JSON file from a tar archive.

    Args:
        filename (str): Path to the tar archive
        select_json (int, optional): Index of the JSON file to use if multiple are found
        auto_select (bool): If True and multiple JSON files are found, automatically select
                           the first one without prompting. Default is True.

    Returns:
        dict: Contents of the JSON file

    Raises:
        tarfile.ReadError: If the file is not a valid tar archive
        KeyError: If the specified JSON file is not found in the archive
        IndexError: If no JSON files are found in the tar
        json.JSONDecodeError: If the file is not valid JSON
    """
    try:
        with tarfile.open(filename) as tar:
            # Find files inside the tar
            tar_contents = tar.getnames()

            # Only get the files with .json extension
            pattern = re.compile(r'.*\.json')
            tar_files = list(filter(pattern.match, tar_contents))

            if not tar_files:
                logger.error("No JSON files found in the tar archive")
                raise IndexError("No JSON files found in the tar archive")

            # If multiple JSON files are found, handle selection
            if len(tar_files) > 1:
                if select_json is not None and 0 <= select_json < len(tar_files):
                    selected_index = select_json
                elif auto_select:
                    selected_index = 0
                    logger.info(f"Multiple JSON files found. Auto-selecting: {tar_files[selected_index]}")
                else:
                    # This branch is for interactive use, which should be rare in automated systems
                    logger.info("Multiple JSON files found in the tar archive:")
                    for i, file in enumerate(tar_files):
                        logger.info(f"{i+1}: {file}")

                    while True:
                        try:
                            selection = input("Enter the number of the JSON file to use: ")
                            selected_index = int(selection) - 1
                            if 0 <= selected_index < len(tar_files):
                                break
                            logger.error("Invalid selection. Please enter a valid number.")
                        except ValueError:
                            logger.error("Please enter a number.")
            else:
                selected_index = 0

            # Read that file and parse it
            file_obj = tar.extractfile(tar.getmember(tar_files[selected_index]))
            if file_obj is None:
                raise KeyError(f"File {tar_files[selected_index]} could not be extracted")

            data = json.loads(file_obj.read().decode('utf-8'))
            return data
    except tarfile.ReadError as e:
        logger.error(f"Invalid tar file: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in tar file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading tar file {filename}: {e}")
        raise

def read_tarfile_object(file_obj: BinaryIO, select_json: Optional[int] = None,
                       auto_select: bool = True) -> Dict[str, Any]:
    """
    Extract and read a JSON file from a tar archive provided as a file-like object.
    This is useful for processing uploaded files without saving them to disk.

    Args:
        file_obj (BinaryIO): File-like object containing a tar archive
        select_json (int, optional): Index of the JSON file to use if multiple are found
        auto_select (bool): If True and multiple JSON files are found, automatically select
                           the first one without prompting. Default is True.

    Returns:
        dict: Contents of the JSON file

    Raises:
        tarfile.ReadError: If the content is not a valid tar archive
        KeyError: If the specified JSON file is not found in the archive
        IndexError: If no JSON files are found in the tar
        json.JSONDecodeError: If the file is not valid JSON
    """
    # Create a temporary file to store the tar content
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            # Reset file pointer to beginning
            file_obj.seek(0)

            # Write content to temporary file
            temp_file.write(file_obj.read())
            temp_file.flush()

            # Use the existing read_tarfile function with the temporary file
            return read_tarfile(temp_file.name, select_json, auto_select)
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file.name}: {e}")

def extract_tar_contents(tar_filename: str, output_dir: Optional[str] = None,
                        file_pattern: Optional[str] = None) -> List[str]:
    """
    Extract contents from a tar file based on an optional pattern.

    Args:
        tar_filename (str): Path to the tar file
        output_dir (str, optional): Directory to extract files to. If None, files are not extracted.
        file_pattern (str, optional): Regex pattern to match filenames

    Returns:
        list: List of extracted file paths or tar members if output_dir is None
    """
    try:
        with tarfile.open(tar_filename) as tar:
            # Get all members
            members = tar.getmembers()

            # Filter members if pattern is provided
            if file_pattern:
                pattern = re.compile(file_pattern)
                members = [m for m in members if pattern.match(m.name)]

            # Extract if output_dir is provided
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                tar.extractall(path=output_dir, members=members)
                return [os.path.join(output_dir, m.name) for m in members]
            else:
                return [m.name for m in members]
    except tarfile.ReadError as e:
        logger.error(f"Invalid tar file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error extracting from tar file {tar_filename}: {e}")
        raise

def extract_tar_object(file_obj: BinaryIO, output_dir: str,
                      file_pattern: Optional[str] = None) -> List[str]:
    """
    Extract contents from a tar file provided as a file-like object.
    This is useful for processing uploaded files without saving them to disk.

    Args:
        file_obj (BinaryIO): File-like object containing a tar archive
        output_dir (str): Directory to extract files to
        file_pattern (str, optional): Regex pattern to match filenames

    Returns:
        list: List of extracted file paths
    """
    # Create a temporary file to store the tar content
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            # Reset file pointer to beginning
            file_obj.seek(0)

            # Write content to temporary file
            temp_file.write(file_obj.read())
            temp_file.flush()

            # Use the existing extract_tar_contents function with the temporary file
            return extract_tar_contents(temp_file.name, output_dir, file_pattern)
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file.name}: {e}")

def list_tar_contents(tar_filename: str, file_pattern: Optional[str] = None) -> List[str]:
    """
    List contents of a tar file, optionally filtered by a pattern.

    Args:
        tar_filename (str): Path to the tar file
        file_pattern (str, optional): Regex pattern to match filenames

    Returns:
        list: List of file names in the tar archive
    """
    try:
        with tarfile.open(tar_filename) as tar:
            contents = tar.getnames()

            # Filter contents if pattern is provided
            if file_pattern:
                pattern = re.compile(file_pattern)
                contents = [name for name in contents if pattern.match(name)]

            return contents
    except tarfile.ReadError as e:
        logger.error(f"Invalid tar file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error listing tar file {tar_filename}: {e}")
        raise

def list_tar_object(file_obj: BinaryIO, file_pattern: Optional[str] = None) -> List[str]:
    """
    List contents of a tar file provided as a file-like object.
    This is useful for processing uploaded files without saving them to disk.

    Args:
        file_obj (BinaryIO): File-like object containing a tar archive
        file_pattern (str, optional): Regex pattern to match filenames

    Returns:
        list: List of file names in the tar archive
    """
    # Create a temporary file to store the tar content
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            # Reset file pointer to beginning
            file_obj.seek(0)

            # Write content to temporary file
            temp_file.write(file_obj.read())
            temp_file.flush()

            # Use the existing list_tar_contents function with the temporary file
            return list_tar_contents(temp_file.name, file_pattern)
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file.name}: {e}")