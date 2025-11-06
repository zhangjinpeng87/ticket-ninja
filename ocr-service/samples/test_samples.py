#!/usr/bin/env python3
"""
Test script to send sample images to the OCR service and display results.
Usage: python test_samples.py [ocr_service_url]

Note: Make sure you're using the same Python that has the 'requests' module installed.
If using anaconda/conda, use the Python from that environment.
"""

import sys
import os
import requests
import json
from pathlib import Path

def test_ocr_service(image_path, ocr_service_url="http://localhost:8001"):
    """Test OCR service with a sample image."""
    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(image_path)}")
    print(f"{'='*60}")
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f, 'image/png')}
            response = requests.post(
                f"{ocr_service_url}/extract-error-logs",
                files=files,
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Success!")
            print(f"\nError Summary: {result.get('error_summary', 'N/A')}")
            print(f"Confidence: {result.get('confidence', 0.0):.2f}")
            print(f"\nError Lines Found ({len(result.get('error_lines', []))}):")
            for i, line in enumerate(result.get('error_lines', [])[:5], 1):
                print(f"  {i}. {line[:80]}...")
            if len(result.get('error_lines', [])) > 5:
                print(f"  ... and {len(result.get('error_lines', [])) - 5} more")
            
            print(f"\nFull Text (first 200 chars):")
            full_text = result.get('full_text', '')
            print(f"  {full_text[:200]}...")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Could not connect to OCR service at {ocr_service_url}")
        print(f"   Make sure the OCR service is running!")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Main function to test all samples."""
    # Get OCR service URL from command line or use default
    ocr_service_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"
    
    # Get samples directory
    samples_dir = Path(__file__).parent
    
    # Find all PNG sample images
    sample_images = list(samples_dir.glob("sample_*.png"))
    
    if not sample_images:
        print("No sample images found!")
        print("Please run 'python generate_samples.py' first to generate sample images.")
        return
    
    print(f"Found {len(sample_images)} sample images")
    print(f"Testing against OCR service: {ocr_service_url}")
    
    # Test each sample
    results = []
    for image_path in sorted(sample_images):
        success = test_ocr_service(image_path, ocr_service_url)
        results.append((os.path.basename(image_path), success))
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    for filename, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {filename}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {passed}/{total} passed")

if __name__ == "__main__":
    main()

