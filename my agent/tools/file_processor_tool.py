#!/usr/bin/env python3
"""
Actual Google ADK Tool for File Processing
Implements a real tool that can be used by Google ADK agents to process documents
"""

import os
import mimetypes
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext


class FileProcessorTool(BaseTool):
    """A Google ADK tool for processing various file types (PDF, DOCX, TXT, etc.)"""
    
    def __init__(self):
        super().__init__(
            name="file_processor",
            description="Process uploaded files and extract text content from PDF, DOCX, TXT, and other formats"
        )
    
    async def _run_async_impl(self, *, args: Dict[str, Any], tool_context: ToolContext) -> Dict[str, Any]:
        """
        Execute the file processing tool
        
        Args:
            args: Dictionary containing 'file_path' (str) and optionally 'extract_metadata' (bool)
            tool_context: Context for the tool execution
            
        Returns:
            Dictionary with extracted file content and metadata
        """
        file_path = args.get("file_path", "")
        extract_metadata = args.get("extract_metadata", True)
        
        if not file_path:
            return {
                "status": "error",
                "error_message": "File path parameter is required"
            }
        
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "error_message": f"File not found: {file_path}",
                "evidence": [f"Attempted to access file: {file_path}"]
            }
        
        try:
            # Get file information
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Extract content based on file type
            extracted_content = ""
            metadata = {}
            
            if file_path.lower().endswith('.txt'):
                extracted_content = await self._process_text_file(file_path)
            elif file_path.lower().endswith('.pdf'):
                extracted_content = await self._process_pdf_file(file_path)
            elif file_path.lower().endswith(('.docx', '.doc')):
                extracted_content = await self._process_docx_file(file_path)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                extracted_content = await self._process_xlsx_file(file_path)
            else:
                # Try to read as text for other formats
                try:
                    extracted_content = await self._process_text_file(file_path)
                except UnicodeDecodeError:
                    extracted_content = f"[Binary file content - {file_size} bytes]"
            
            # Extract metadata if requested
            if extract_metadata:
                metadata = {
                    "file_name": file_name,
                    "file_size": file_size,
                    "mime_type": mime_type,
                    "file_extension": os.path.splitext(file_path)[1].lower()
                }
            
            # Store evidence in session state
            tool_context.state["last_processed_file"] = file_path
            tool_context.state["last_extracted_content_length"] = len(extracted_content)
            
            return {
                "status": "success",
                "file_path": file_path,
                "content": extracted_content,
                "metadata": metadata,
                "evidence": [
                    f"File processed: {file_name}",
                    f"File type: {mime_type or 'unknown'}",
                    f"Content extracted: {len(extracted_content)} characters"
                ]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"File processing failed: {str(e)}",
                "evidence": [f"File processing attempt failed for: {file_path}"]
            }
    
    async def _process_text_file(self, file_path: str) -> str:
        """Process a plain text file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    async def _process_pdf_file(self, file_path: str) -> str:
        """Process a PDF file using pypdf/PyPDF2 when available."""
        try:
            try:
                from pypdf import PdfReader
            except ImportError:
                from PyPDF2 import PdfReader

            reader = PdfReader(file_path)
            pages = []
            for index, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(f"[Page {index}]\n{text.strip()}")
            if not pages:
                return "[PDF parsed, but no extractable text was found]"
            return "\n\n".join(pages)
        except ImportError:
            return "[PDF parser dependency is not installed. Install pypdf to extract PDF text.]"
    
    async def _process_docx_file(self, file_path: str) -> str:
        """Process a DOCX file using python-docx or a ZIP/XML fallback."""
        try:
            from docx import Document

            document = Document(file_path)
            text = "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())
            return text or "[DOCX parsed, but no paragraph text was found]"
        except ImportError:
            if not file_path.lower().endswith(".docx"):
                return "[DOC parser dependency is not installed. Use DOCX or install python-docx.]"
            try:
                with zipfile.ZipFile(file_path) as archive:
                    xml_bytes = archive.read("word/document.xml")
                root = ET.fromstring(xml_bytes)
                namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                text_nodes = [node.text for node in root.findall(".//w:t", namespace) if node.text]
                return "\n".join(text_nodes) or "[DOCX parsed, but no text nodes were found]"
            except Exception as exc:
                return f"[DOCX fallback extraction failed: {exc}]"

    async def _process_xlsx_file(self, file_path: str) -> str:
        """Process an XLSX file using openpyxl or a ZIP/XML fallback."""
        if file_path.lower().endswith(".xls"):
            return "[Legacy XLS parsing is not installed. Convert to CSV or XLSX for extraction.]"

        try:
            from openpyxl import load_workbook

            workbook = load_workbook(file_path, read_only=True, data_only=True)
            rows = []
            for sheet in workbook.worksheets:
                rows.append(f"[Sheet: {sheet.title}]")
                for row in sheet.iter_rows(values_only=True):
                    values = [str(value) for value in row if value is not None]
                    if values:
                        rows.append(", ".join(values))
                rows.append("")
            return "\n".join(rows).strip() or "[XLSX parsed, but no cell values were found]"
        except ImportError:
            try:
                with zipfile.ZipFile(file_path) as archive:
                    shared_strings = []
                    if "xl/sharedStrings.xml" in archive.namelist():
                        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                        namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                        for item in root.findall(".//main:si", namespace):
                            text = "".join(node.text or "" for node in item.findall(".//main:t", namespace))
                            shared_strings.append(text)

                    rows = []
                    sheet_names = [
                        name for name in archive.namelist()
                        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
                    ]
                    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                    for sheet_name in sheet_names:
                        rows.append(f"[Sheet: {sheet_name}]")
                        root = ET.fromstring(archive.read(sheet_name))
                        for row in root.findall(".//main:row", namespace):
                            values = []
                            for cell in row.findall("main:c", namespace):
                                value_node = cell.find("main:v", namespace)
                                if value_node is None or value_node.text is None:
                                    continue
                                if cell.attrib.get("t") == "s":
                                    index = int(value_node.text)
                                    values.append(shared_strings[index] if index < len(shared_strings) else value_node.text)
                                else:
                                    values.append(value_node.text)
                            if values:
                                rows.append(", ".join(values))
                        rows.append("")
                    return "\n".join(rows).strip() or "[XLSX parsed, but no cell values were found]"
            except Exception as exc:
                return f"[XLSX fallback extraction failed: {exc}]"


# Create a singleton instance for use by agents
file_processor_tool = FileProcessorTool()
