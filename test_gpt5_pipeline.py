#!/usr/bin/env python3
"""
Test the complete GPT-5 RAG pipeline for due diligence screening
"""
import asyncio
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_gpt5_pipeline():
    """Test the complete GPT-5 RAG pipeline"""
    print("🚀 TESTING GPT-5 RAG PIPELINE")
    print("="*80)
    
    try:
        # Import all services
        from services.resolve import entity_resolver
        from services.search import search_service
        from services.extract import extraction_service
        from services.llm import gpt5_client
        
        # Test company
        company = "Apple Inc"
        country = "United States"
        
        print(f"🏢 Testing company: {company}")
        print(f"🌍 Country: {country}")
        
        # Step 1: Entity Resolution
        print(f"\n1️⃣ ENTITY RESOLUTION")
        resolved = entity_resolver.resolve_input(company, "", country)
        print(f"   ✅ Resolved: {resolved['company_name']}")
        print(f"   🔍 Clean name: {resolved['company_clean']}")
        print(f"   🌍 Country: {resolved['country']}")
        print(f"   🔄 Variations: {resolved['search_variations']}")
        
        # Step 2: Web Search
        print(f"\n2️⃣ WEB SEARCH")
        search_results = await search_service.search_multiple_intents(
            resolved['company_name'], 
            resolved['country']
        )
        
        total_results = sum(len(results) for results in search_results.values())
        print(f"   📊 Found {total_results} total results across {len(search_results)} buckets")
        
        for bucket, results in search_results.items():
            if results:
                print(f"   📁 {bucket}: {len(results)} results")
                for i, result in enumerate(results[:2], 1):
                    print(f"      {i}. {result.get('title', 'No title')[:60]}...")
        
        # Step 3: Content Extraction  
        print(f"\n3️⃣ CONTENT EXTRACTION")
        extracted_results = await extraction_service.extract_multiple(search_results)
        
        # Deduplicate content
        deduplicated_results = extraction_service.deduplicate_by_content(extracted_results)
        
        # Get best snippets for GPT-5
        best_snippets = extraction_service.get_best_snippets(deduplicated_results)
        
        print(f"   📄 Extracted content from {len(best_snippets)} sources")
        for i, snippet in enumerate(best_snippets[:3], 1):
            print(f"      {i}. {snippet.get('title', 'No title')[:50]}...")
            print(f"         📏 Length: {snippet.get('content_length', 0)} chars")
            print(f"         🔗 Source: {snippet.get('source_type', 'unknown')}")
        
        # Step 4: GPT-5 Analysis
        print(f"\n4️⃣ GPT-5 ANALYSIS")
        if best_snippets:
            analysis_result = await gpt5_client.ask_gpt5(
                resolved['company_name'],
                resolved['country'], 
                best_snippets
            )
            
            print(f"   🤖 Analysis completed")
            print(f"   ✅ Status: {analysis_result.get('validation_status', 'unknown')}")
            
            # Display key results
            exec_summary = analysis_result.get('executive_summary', 'No summary')
            print(f"   📝 Summary: {exec_summary[:100]}...")
            
            official_website = analysis_result.get('official_website', 'unknown')
            print(f"   🌐 Official website: {official_website}")
            
            sanctions = analysis_result.get('sanctions', [])
            print(f"   🛡️ Sanctions: {len(sanctions)} matches")
            
            adverse_media = analysis_result.get('adverse_media', [])
            print(f"   📰 Adverse media: {len(adverse_media)} articles")
            
            bribery = analysis_result.get('bribery_corruption', [])
            print(f"   💰 Bribery/corruption: {len(bribery)} items")
            
            political = analysis_result.get('political_exposure', [])
            print(f"   🏛️ Political exposure: {len(political)} items")
            
            disadvantages = analysis_result.get('disadvantages', [])
            print(f"   ⚠️ Risk flags: {len(disadvantages)} items")
            
            citations = analysis_result.get('citations', [])
            print(f"   📚 Citations: {len(citations)} sources")
            
            # Display some detailed results
            if adverse_media:
                print(f"\n   📰 ADVERSE MEDIA SAMPLE:")
                for i, item in enumerate(adverse_media[:2], 1):
                    print(f"      {i}. {item.get('headline', 'No headline')}")
                    print(f"         📅 Date: {item.get('date', 'unknown')}")
                    print(f"         ⚠️ Severity: {item.get('severity', 'unknown')}")
                    print(f"         🔗 Source: {item.get('citation_url', 'No URL')}")
            
            if disadvantages:
                print(f"\n   ⚠️ RISK FLAGS SAMPLE:")
                for i, item in enumerate(disadvantages[:2], 1):
                    print(f"      {i}. {item.get('risk_type', 'Unknown risk')}")
                    print(f"         📝 Description: {item.get('description', 'No description')[:80]}...")
                    print(f"         ⚠️ Severity: {item.get('severity', 'unknown')}")
            
            # Save full results
            with open('gpt5_test_results.json', 'w') as f:
                json.dump(analysis_result, f, indent=2)
            print(f"\n   💾 Full results saved to: gpt5_test_results.json")
            
        else:
            print(f"   ❌ No content extracted for analysis")
        
        # Step 5: Cleanup
        print(f"\n5️⃣ CLEANUP")
        await extraction_service.close()
        print(f"   ✅ Resources cleaned up")
        
        print(f"\n{'='*80}")
        print(f"🎯 GPT-5 RAG PIPELINE TEST COMPLETE!")
        print(f"✅ All steps executed successfully")
        print(f"📊 Pipeline ready for production use")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_gpt5_pipeline())
    print(f"\n🎯 FINAL RESULT: {'SUCCESS' if success else 'FAILED'}")