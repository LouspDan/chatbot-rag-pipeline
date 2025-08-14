"""
Configuration pytest pour tests chatbot RAG pipeline
"""

import pytest
import sys
import os

# Ajouter le dossier racine au PYTHONPATH (depuis tests/ vers racine)
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# Vérification debug
print(f"🔧 PYTHONPATH ajouté: {root_dir}")

@pytest.fixture(scope="session")
def db_config():
    """Configuration base de données pour tests"""
    return {
        'host': 'localhost',
        'port': 5432,
        'database': 'chatbot_db',
        'user': 'chatbot_user',
        'password': 'chatbot_password'
    }

@pytest.fixture(scope="session") 
def test_document():
    """Document de test pour les tests"""
    from src.data_extraction.extractors.service_public import ServicePublicExtractor
    
    extractor = ServicePublicExtractor()
    doc = extractor.extract_single_test_fiche()
    
    if not doc:
        pytest.skip("Impossible de récupérer document de test")
    
    return doc