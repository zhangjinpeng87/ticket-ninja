from typing import Dict, Optional
import httpx
import os
from fastapi import HTTPException

# OCR Service URL - can be overridden via environment variable
OCR_SERVICE_URL = os.getenv("OCR_SERVICE_URL", "http://localhost:8001")

async def parse_screenshot(screenshot_id: str) -> Optional[Dict[str, str]]:
    """
    Fetch screenshot by ID and send it to OCR service for error log extraction.
    
    Args:
        screenshot_id: Identifier for the screenshot (could be URL, file path, or base64 data)
    
    Returns:
        Dictionary containing error_summary and other extracted information
    """
    try:
        # For now, we assume screenshot_id is a base64-encoded image or a URL
        # In production, you'd fetch the actual image binary from storage/URL
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Option 1: If screenshot_id is a URL, fetch it first
            if screenshot_id.startswith("http://") or screenshot_id.startswith("https://"):
                # Fetch image from URL
                response = await client.get(screenshot_id)
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to fetch screenshot from URL: {screenshot_id}"
                    )
                image_data = response.content
                
                # Send to OCR service
                files = {"file": ("screenshot.png", image_data, "image/png")}
                ocr_response = await client.post(
                    f"{OCR_SERVICE_URL}/extract-error-logs",
                    files=files
                )
            
            # Option 2: If screenshot_id is base64 encoded
            elif screenshot_id.startswith("data:image/") or len(screenshot_id) > 100:
                # Assume it's base64 data
                ocr_response = await client.post(
                    f"{OCR_SERVICE_URL}/extract-error-logs-base64",
                    json={"image_data": screenshot_id}
                )
            
            # Option 3: If it's a file path or storage ID, you'd need to fetch it
            else:
                # Placeholder: In production, fetch from storage service
                # For now, return a placeholder
                return {
                    "error_summary": f"[Screenshot ID: {screenshot_id}] Could not process: storage fetch not implemented",
                    "full_text": "",
                    "error_lines": [],
                    "confidence": 0.0
                }
            
            if ocr_response.status_code != 200:
                raise HTTPException(
                    status_code=ocr_response.status_code,
                    detail=f"OCR service error: {ocr_response.text}"
                )
            
            ocr_result = ocr_response.json()
            
            return {
                "error_summary": ocr_result.get("error_summary", ""),
                "full_text": ocr_result.get("full_text", ""),
                "error_lines": ocr_result.get("error_lines", []),
                "confidence": ocr_result.get("confidence", 0.0)
            }
    
    except httpx.RequestError as e:
        # OCR service might not be available
        return {
            "error_summary": f"[Screenshot] OCR service unavailable: {str(e)}",
            "full_text": "",
            "error_lines": [],
            "confidence": 0.0
        }
    except Exception as e:
        return {
            "error_summary": f"[Screenshot] Processing error: {str(e)}",
            "full_text": "",
            "error_lines": [],
            "confidence": 0.0
        }
