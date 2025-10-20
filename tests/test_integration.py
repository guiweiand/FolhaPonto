"""
Integration Test for File Upload Functionality

This script tests the complete workflow:
1. Import and use the pdf_processor module
2. Test file upload simulation
3. Verify data processing
4. Check file generation
"""

import sys
import os
from pathlib import Path

# Add the dashboard directory to Python path so we can import our modules
dashboard_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dashboard')
sys.path.append(dashboard_dir)

from pdf_processor import process_uploaded_pdf
import json
import tempfile
import shutil

def test_upload_workflow():
    """Test the complete upload workflow"""
    print("🧪 Testing PDF Upload Integration...")
    
    # 1. Test with the sample PDF file - update path to be relative to tests directory
    pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test_sample', 'Ficha_Ponto_Simplificada_André_Luis.pdf')
    
    if not os.path.exists(pdf_path):
        print(f"❌ Test PDF not found: {pdf_path}")
        return False
    
    print(f"✅ Found test PDF: {pdf_path}")
    
    # 2. Test the processing function (simulates upload workflow)
    try:
        print("🔄 Processing PDF...")
        webapp_data, status_msg = process_uploaded_pdf(pdf_path)
        
        if webapp_data is None:
            print(f"❌ Processing failed: {status_msg}")
            return False
            
        print("✅ PDF processing successful!")
        print(f"📊 Status: {status_msg}")
        
        # 3. Verify the data structure
        required_keys = [
            'company', 'employee', 'period', 'timesheet_data',
            'compliance_summary', 'metadata'
        ]
        
        for key in required_keys:
            if key not in webapp_data:
                print(f"❌ Missing required key: {key}")
                return False
        
        print("✅ Data structure validation passed!")
        
        # 4. Check specific data points
        timesheet_count = len(webapp_data.get('timesheet_data', []))
        compliance_issues = webapp_data.get('compliance_summary', {}).get('total_compliance_issues', 0)
        employee_name = webapp_data.get('employee', {}).get('name', 'Unknown')
        
        print(f"📈 Data Summary:")
        print(f"   - Timesheet records: {timesheet_count}")
        print(f"   - Compliance issues: {compliance_issues}")
        print(f"   - Employee: {employee_name}")
        
        # 5. Verify that JSON file was created in the correct location
        expected_json_path = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "timesheet_webapp_data.json"))
        if expected_json_path.exists():
            print(f"✅ JSON file created successfully: {expected_json_path}")
            
            # Check file timestamp
            from datetime import datetime
            mod_time = datetime.fromtimestamp(os.path.getmtime(expected_json_path))
            print(f"   Last modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"⚠️ JSON file not found at expected location: {expected_json_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        return False

def test_file_upload_simulation():
    """Simulate the file upload process that happens in Streamlit"""
    print("\n🔄 Testing File Upload Simulation...")
    
    try:
        # Simulate reading a PDF file (like Streamlit's file_uploader does)
        pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test_sample', 'Ficha_Ponto_Simplificada_André_Luis.pdf')
        
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        print(f"📄 Read PDF file: {len(pdf_bytes)} bytes")
        
        # Simulate the upload process using temporary file (like our handle_pdf_upload function)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_bytes)
            temp_file_path = temp_file.name
        
        print(f"💾 Created temporary file: {temp_file_path}")
        
        # Process the temporary file
        webapp_data, status_msg = process_uploaded_pdf(temp_file_path)
        
        # Clean up
        os.unlink(temp_file_path)
        print("🧹 Cleaned up temporary file")
        
        if webapp_data:
            print("✅ File upload simulation successful!")
            return True
        else:
            print(f"❌ File upload simulation failed: {status_msg}")
            return False
            
    except Exception as e:
        print(f"❌ Upload simulation error: {str(e)}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Starting Integration Tests...\n")
    
    # Test 1: Basic upload workflow
    test1_result = test_upload_workflow()
    
    # Test 2: File upload simulation
    test2_result = test_file_upload_simulation()
    
    # Summary
    print("\n" + "="*50)
    print("📋 TEST RESULTS SUMMARY")
    print("="*50)
    print(f"Basic Upload Workflow: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"File Upload Simulation: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    overall_result = test1_result and test2_result
    print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if overall_result else '⚠️ SOME TESTS FAILED'}")
    
    if overall_result:
        print("\n✅ Integration is ready for user testing!")
        print("🌐 The Streamlit app should now support:")
        print("   - PDF file upload via sidebar")
        print("   - Automatic processing and analysis")
        print("   - Dashboard refresh with new data")
        print("   - Status indicators and error handling")
    
    return overall_result

if __name__ == "__main__":
    main()