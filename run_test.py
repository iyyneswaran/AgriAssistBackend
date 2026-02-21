import asyncio
import sys
import os

sys.path.insert(0, r'c:\Users\Dheepa\OneDrive\Desktop\AgriAssist_Backend\AgriAssistBackend\Chat')
os.chdir(r'c:\Users\Dheepa\OneDrive\Desktop\AgriAssist_Backend\AgriAssistBackend\Chat')

from dotenv import load_dotenv
load_dotenv('.env')

import app.db.base
from app.services.rag.ag_service import RagService
from app.db.models.user import User

async def main():
    user = User(
        id='test-id',
        name='Test Farmer',
        phone_number='+919876543210',
        region='Pan India',
        crop_type='Various',
        land_size=4.0
    )
    svc = RagService()
    result = await svc.recommend_schemes(
        query='What is the Seed Multiplication Scheme?',
        user=user,
        db=None,
        top_k=5
    )

    # Write output to a UTF-8 file
    with open(r'c:\Users\Dheepa\OneDrive\Desktop\AgriAssist_Backend\AgriAssistBackend\pinecone_test_output.txt', 'w', encoding='utf-8') as f:
        f.write('=== ANSWER ===\n')
        f.write(result.get('answer', 'No answer') + '\n\n')
        f.write('=== SOURCES ===\n')
        for d in result.get('source_documents', []):
            f.write(f"  - {d.get('title', 'N/A')} (Score: {d.get('similarity', 0):.3f})\n")
            f.write(f"    Region: {d.get('region', 'N/A')}\n")
            f.write(f"    Eligibility: {d.get('eligibility', 'N/A')}\n")
            f.write(f"    Crop Type: {d.get('crop_type', 'N/A')}\n")

    print("Test complete! Results written to pinecone_test_output.txt")

asyncio.run(main())
