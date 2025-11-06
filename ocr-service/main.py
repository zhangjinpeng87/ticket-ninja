from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import io
import re
import os
import numpy as np
from PIL import Image
import easyocr

app = FastAPI(title="OCR Service - Error Log Recognition", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize EasyOCR reader (English only for now, can add more languages)
reader = easyocr.Reader(['en'], gpu=False)

class ErrorLogResponse(BaseModel):
    error_summary: str
    full_text: str
    error_lines: List[str]
    confidence: float

def extract_error_logs(text: str) -> Dict[str, Any]:
    """
    Extract error log patterns from OCR text.
    Looks for common error indicators: Exception, Error, Traceback, etc.
    """
    lines = text.split('\n')
    error_lines = []
    error_keywords = [
        r'error', r'exception', r'traceback', r'fatal', r'critical',
        r'failed', r'failure', r'timeout', r'nullpointer', r'undefined',
        r'stack trace', r'stacktrace', r'at .*\.java', r'at .*\.py',
        r'\d{4}-\d{2}-\d{2}.*error', r'\[error\]', r'\[ERROR\]',
        r'errno', r'socket.*error', r'connection.*refused'
    ]
    
    for line in lines:
        line_lower = line.lower()
        if any(re.search(pattern, line_lower, re.IGNORECASE) for pattern in error_keywords):
            error_lines.append(line.strip())
    
    # Generate error summary
    if error_lines:
        # Try to extract the most relevant error line
        primary_error = error_lines[0] if error_lines else ""
        # Look for exception type or error message
        exception_match = re.search(r'([A-Z][a-zA-Z]*Error|[A-Z][a-zA-Z]*Exception)', primary_error)
        if exception_match:
            error_type = exception_match.group(1)
            # Try to find location or context
            location_match = re.search(r'at\s+(.+?)(?:\s|$)', primary_error)
            location = location_match.group(1) if location_match else ""
            error_summary = f"Detected error: {error_type}"
            if location:
                error_summary += f" at {location}"
        else:
            # Use first line or truncated version
            error_summary = error_lines[0][:200] if error_lines[0] else "Error detected in screenshot"
    else:
        error_summary = "No clear error patterns detected in screenshot"
    
    return {
        "error_summary": error_summary,
        "error_lines": error_lines,
        "confidence": 0.8 if error_lines else 0.3
    }

@app.get("/health")
async def health():
    return {"ok": True, "service": "ocr-service"}

@app.post("/extract-error-logs", response_model=ErrorLogResponse)
async def extract_error_logs_from_screenshot(file: UploadFile = File(...)):
    """
    Receive a screenshot image and extract error log text using OCR.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image data
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (EasyOCR requires RGB)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert PIL Image to numpy array (EasyOCR requires numpy array)
        image_array = np.array(image)
        
        # Perform OCR
        results = reader.readtext(image_array)
        
        # Extract text from OCR results
        full_text = '\n'.join([detection[1] for detection in results])
        
        # Extract error logs
        error_info = extract_error_logs(full_text)
        
        return ErrorLogResponse(
            error_summary=error_info["error_summary"],
            full_text=full_text,
            error_lines=error_info["error_lines"],
            confidence=error_info["confidence"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@app.post("/extract-error-logs-base64")
async def extract_error_logs_base64(request: dict):
    """
    Alternative endpoint that accepts base64 encoded image data.
    """
    import base64
    
    if "image_data" not in request:
        raise HTTPException(status_code=400, detail="Missing 'image_data' field with base64 string")
    
    try:
        # Decode base64 image
        image_data = base64.b64decode(request["image_data"].split(",")[-1] if "," in request["image_data"] else request["image_data"])
        image = Image.open(io.BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert PIL Image to numpy array (EasyOCR requires numpy array)
        image_array = np.array(image)
        
        # Perform OCR
        results = reader.readtext(image_array)
        full_text = '\n'.join([detection[1] for detection in results])
        
        # Extract error logs
        error_info = extract_error_logs(full_text)
        
        return ErrorLogResponse(
            error_summary=error_info["error_summary"],
            full_text=full_text,
            error_lines=error_info["error_lines"],
            confidence=error_info["confidence"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host=host, port=port)
