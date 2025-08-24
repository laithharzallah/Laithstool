#!/usr/bin/env python3
"""
Test the complete GPT-5 RAG pipeline for due diligence screening
Enhanced version with better error handling and Serper API
"""
import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_rawabi_holding_enhanced():
    """Test Rawabi Holding with enhanced GPT-5 RAG pipeline"""
    print("🇸🇦 TESTING RAWABI HOLDING (SAUDI ARABIA) - ENHANCED VERSION")
    print("="*80)
    
    try:
        # Check environment
        print("🔧 ENVIRONMENT CHECK:")
        openai_key = os.getenv("OPENAI_API_KEY")
        serper_key = os.getenv("SERPER_API_KEY")
        search_provider = os.getenv("SEARCH_PROVIDER")
        
        print(f"   OpenAI API: {'✅ Configured' if openai_key else '❌ Missing'}")
        print(f"   Serper API: {'✅ Configured' if serper_key else '❌ Missing'}")
        print(f"   Search Provider: {search_provider or 'Not set'}")
        
        # Import services
        from services.resolve import entity_resolver
        from services.search import search_service
        from services.extract import extraction_service
        from services.llm import gpt5_client
        
        company = "Rawabi Holding"
        country = "Saudi Arabia"
        
        # Step 1: Entity Resolution
        print("\n1️⃣ ENTITY RESOLUTION")
        resolved = entity_resolver.resolve_input(company, "", country)
        print(f"   ✅ Resolved: {resolved['company_name']} | {resolved['country']}")
        
        # Step 2: Multi-Intent Web Search
        print("\n2️⃣ ENHANCED WEB SEARCH")
        search_results = await search_service.search_multiple_intents(company, country)
        
        total_results = sum(len(results) for results in search_results.values())
        print(f"   📊 Total Results: {total_results}")
        
        # Show sample results per bucket
        for bucket, results in search_results.items():
            if results:
                print(f"   📁 {bucket}: {len(results)} results")
                for i, result in enumerate(results[:1], 1):
                    title = result.get('title', 'No title')[:60]
                    url = result.get('url', 'No URL')[:50]
                    print(f"      {i}. {title}...")
                    print(f"         🔗 {url}...")
        
        # Step 3: Content Extraction with Enhanced Error Handling
        print("\n3️⃣ CONTENT EXTRACTION")
        extracted_results = await extraction_service.extract_multiple(search_results)
        
        # Count successful extractions
        successful_extractions = 0
        for bucket, results in extracted_results.items():
            for result in results:
                if result.get('extraction_success'):
                    successful_extractions += 1
        
        print(f"   📄 Successful Extractions: {successful_extractions}")
        
        # Deduplicate and get best snippets
        deduplicated_results = extraction_service.deduplicate_by_content(extracted_results)
        best_snippets = extraction_service.get_best_snippets(deduplicated_results)
        
        print(f"   📝 Best Snippets Selected: {len(best_snippets)}")
        
        # Show sample snippets
        for i, snippet in enumerate(best_snippets[:3], 1):
            title = snippet.get('title', 'No title')[:50]
            text_preview = snippet.get('text', '')[:100]
            source_type = snippet.get('source_type', 'unknown')
            print(f"   {i}. [{source_type}] {title}...")
            print(f"      📝 {text_preview}...")
        
        # Step 4: GPT-5 Analysis
        print("\n4️⃣ GPT-5 ANALYSIS")
        if best_snippets:
            analysis_result = await gpt5_client.ask_gpt5(company, country, best_snippets)
            
            validation_status = analysis_result.get('validation_status', 'unknown')
            print(f"   🤖 Analysis Status: {validation_status}")
            
            if validation_status != 'error':
                # Executive Summary
                exec_summary = analysis_result.get('executive_summary', 'No summary')
                print(f"   📋 Executive Summary:")
                print(f"      {exec_summary}")
                
                # Key Findings
                website = analysis_result.get('official_website', 'unknown')
                sanctions = analysis_result.get('sanctions', [])
                adverse_media = analysis_result.get('adverse_media', [])
                bribery = analysis_result.get('bribery_corruption', [])
                political = analysis_result.get('political_exposure', [])
                disadvantages = analysis_result.get('disadvantages', [])
                citations = analysis_result.get('citations', [])
                
                print(f"\n   🌐 Official Website: {website}")
                print(f"   🛡️ Sanctions: {len(sanctions)} matches")
                print(f"   📰 Adverse Media: {len(adverse_media)} articles") 
                print(f"   💰 Bribery/Corruption: {len(bribery)} items")
                print(f"   🏛️ Political Exposure: {len(political)} items")
                print(f"   ⚠️ Risk Flags: {len(disadvantages)} items")
                print(f"   📚 Citations: {len(citations)} sources")
                
                # Show detailed findings
                if adverse_media:
                    print(f"\n   📰 ADVERSE MEDIA DETAILS:")
                    for i, item in enumerate(adverse_media[:2], 1):
                        headline = item.get('headline', 'No headline')
                        source = item.get('source', 'Unknown')
                        severity = item.get('severity', 'unknown')
                        citation = item.get('citation_url', 'No URL')
                        print(f"      {i}. {headline}")
                        print(f"         📺 {source} | ⚠️ {severity}")
                        print(f"         🔗 {citation}")
                
                if political:
                    print(f"\n   🏛️ POLITICAL EXPOSURE DETAILS:")
                    for i, item in enumerate(political[:2], 1):
                        pol_type = item.get('type', 'Unknown')
                        description = item.get('description', 'No description')[:80]
                        confidence = item.get('confidence', 'unknown')
                        print(f"      {i}. {pol_type}")
                        print(f"         📝 {description}...")
                        print(f"         📊 Confidence: {confidence}")
                
                if disadvantages:
                    print(f"\n   ⚠️ RISK FLAGS DETAILS:")
                    for i, item in enumerate(disadvantages[:2], 1):
                        risk_type = item.get('risk_type', 'Unknown')
                        description = item.get('description', 'No description')[:80]
                        severity = item.get('severity', 'unknown')
                        print(f"      {i}. {risk_type}")
                        print(f"         📝 {description}...")
                        print(f"         ⚠️ Severity: {severity}")
                
                # Save full results
                output_file = 'rawabi_holding_enhanced_results.json'
                with open(output_file, 'w') as f:
                    json.dump(analysis_result, f, indent=2)
                print(f"\n   💾 Full report saved: {output_file}")
                
                return True
            else:
                error_msg = analysis_result.get('error', 'Unknown error')
                print(f"   ❌ GPT-5 Analysis Failed: {error_msg}")
                return False
        else:
            print("   ❌ No content snippets available for analysis")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            await extraction_service.close()
        except:
            pass

async def main():
    """Main test function"""
    print("🚀 ENHANCED GPT-5 RAG PIPELINE TEST")
    print("="*80)
    
    success = await test_rawabi_holding_enhanced()
    
    print(f"\n{'='*80}")
    if success:
        print("🎯 TEST RESULT: ✅ SUCCESS!")
        print("✅ Real internet data collected and analyzed")
        print("✅ GPT-5 synthesis with citations working")
        print("✅ Complete due diligence pipeline functional")
    else:
        print("🎯 TEST RESULT: ❌ FAILED!")
        print("❌ Issues detected in pipeline")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)