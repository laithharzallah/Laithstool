#!/usr/bin/env python3
"""
Quick test script to debug data collection for Siemens AG
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_siemens_data_collection():
    """Test data collection for Siemens AG"""
    print("🔍 Testing data collection for Siemens AG...")
    
    # Check environment variables
    print(f"OpenAI API Key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    print(f"Google API Key: {'✅ Set' if os.getenv('GOOGLE_API_KEY') else '❌ Missing'}")
    print(f"Google CSE ID: {'✅ Set' if os.getenv('GOOGLE_CSE_ID') else '❌ Missing'}")
    
    # Import and test the real data collector
    try:
        from services.real_data import real_data_collector
        
        print("\n📊 Starting comprehensive screening for 'Siemens AG'...")
        result = await real_data_collector.comprehensive_screening("Siemens AG")
        
        print(f"\n✅ Results collected:")
        print(f"- Website: {result.get('website', {}).get('url', 'Not found')}")
        print(f"- Executives: {len(result.get('executives', []))} found")
        print(f"- Sanctions: {len(result.get('sanctions', []))} matches")
        print(f"- Adverse Media: {len(result.get('adverse_media', []))} articles")
        print(f"- AI Summary: {'✅ Generated' if result.get('ai_summary') else '❌ Failed'}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_siemens_data_collection())