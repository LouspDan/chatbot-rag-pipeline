#!/usr/bin/env python3
"""
Test de validation de l'extracteur de base
À placer dans la racine du projet : chatbot-rag-pipeline/
"""

import sys
import os

# Ajouter le dossier racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_extraction.extractors.base_extractor import BaseExtractor

def test_base_extractor():
    """Test de base de notre extracteur"""
    print("🧪 TEST DE L'EXTRACTEUR DE BASE")
    print("=" * 50)
    
    # Initialiser l'extracteur avec un site de test
    extractor = BaseExtractor('https://httpbin.org')
    print("✅ Extracteur initialisé")
    
    # Tester sur une page HTML simple
    test_url = 'https://httpbin.org/html'
    print(f"🔄 Test extraction : {test_url}")
    
    # Extraire le document
    doc = extractor.extract_document(test_url)
    
    if doc:
        print("✅ Extraction réussie !")
        print(f"📄 Titre: {doc.title}")
        print(f"📝 Contenu (50 premiers chars): {doc.content[:50]}...")
        print(f"🏷️ Domaine classifié: {doc.domain}")
        print(f"🔗 URL source: {doc.source_url}")
        print(f"📊 Métadonnées: {doc.metadata}")
    else:
        print("❌ Échec de l'extraction")
        return False
    
    print("\n🎉 TOUS LES TESTS PASSÉS !")
    return True

if __name__ == "__main__":
    success = test_base_extractor()
    sys.exit(0 if success else 1)