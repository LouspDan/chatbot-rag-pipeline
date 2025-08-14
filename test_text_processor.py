#!/usr/bin/env python3
"""
Test du processeur de texte avec nos données Service-Public
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_extraction.extractors.service_public import ServicePublicExtractor
from src.data_processing.text_processor import TextProcessor

def test_text_processor():
    """Test du chunking intelligent avec vraie donnée"""
    print("🧪 TEST PROCESSEUR DE TEXTE")
    print("=" * 50)
    
    # 1. Récupérer un document réel
    print("📄 Extraction d'un document test...")
    extractor = ServicePublicExtractor()
    doc = extractor.extract_single_test_fiche()
    
    if not doc:
        print("❌ Impossible de récupérer un document test")
        return False
    
    print(f"✅ Document récupéré: {doc.title}")
    print(f"📊 Longueur: {len(doc.content)} caractères")
    
    # 2. Initialiser le processeur
    processor = TextProcessor(chunk_size=250, overlap=40)
    print("✅ Processeur initialisé")
    
    # 3. Traiter le document
    print("\n🔄 Chunking du document...")
    chunks = processor.process_document(
        title=doc.title,
        content=doc.content,
        metadata={
            'source_url': doc.source_url,
            'domain': doc.domain,
            'fiche_number': doc.metadata.get('fiche_number')
        }
    )
    
    if not chunks:
        print("❌ Aucun chunk créé")
        return False
    
    print(f"✅ {len(chunks)} chunks créés")
    
    # 4. Analyser les chunks
    print("\n📋 DÉTAIL DES CHUNKS:")
    print("-" * 60)
    
    for i, chunk in enumerate(chunks):
        print(f"\n🔖 Chunk {i+1} ({chunk.chunk_type}):")
        print(f"   📝 Texte: {chunk.text[:100]}...")
        print(f"   📊 Taille: {chunk.char_count} chars, {chunk.word_count} mots")
        print(f"   🏷️ Mots-clés: {', '.join(chunk.keywords)}")
        
        if chunk.metadata.get('is_title'):
            print(f"   👑 TITRE PRINCIPAL")
        
        # Afficher quelques métadonnées intéressantes
        if chunk.metadata.get('has_numbers'):
            print(f"   🔢 Contient des chiffres")
        if chunk.metadata.get('complexity') == 'high':
            print(f"   🧠 Complexité élevée")
    
    # 5. Statistiques globales
    stats = processor.get_processing_stats(chunks)
    
    print(f"\n📊 STATISTIQUES GLOBALES:")
    print("-" * 30)
    print(f"🔢 Total chunks: {stats['total_chunks']}")
    print(f"📏 Caractères totaux: {stats['total_characters']:,}")
    print(f"📝 Mots totaux: {stats['total_words']:,}")
    print(f"📐 Taille moyenne chunk: {stats['avg_chunk_size']} chars")
    
    print(f"\n🏷️ Types de chunks:")
    for chunk_type, count in stats['chunk_types'].items():
        print(f"   - {chunk_type}: {count}")
    
    print(f"\n📏 Distribution tailles:")
    size_dist = stats['size_distribution']
    print(f"   - Petits (<200): {size_dist['small']}")
    print(f"   - Moyens (200-400): {size_dist['medium']}")  
    print(f"   - Grands (>400): {size_dist['large']}")
    
    # 6. Validation qualité
    print(f"\n🔍 VALIDATION QUALITÉ:")
    print("-" * 25)
    
    # Vérifier les tailles
    oversized = [c for c in chunks if c.char_count > 400]
    undersized = [c for c in chunks if c.char_count < 100]
    
    print(f"✅ Chunks bien dimensionnés: {len(chunks) - len(oversized) - len(undersized)}")
    if oversized:
        print(f"⚠️ Chunks trop grands: {len(oversized)}")
    if undersized:
        print(f"⚠️ Chunks trop petits: {len(undersized)}")
    
    # Vérifier la diversité des mots-clés
    all_keywords = set()
    for chunk in chunks:
        all_keywords.update(chunk.keywords)
    
    print(f"🏷️ Diversité mots-clés: {len(all_keywords)} catégories")
    print(f"   Catégories: {', '.join(sorted(all_keywords))}")
    
    print("\n🎉 TEST CHUNKING TERMINÉ AVEC SUCCÈS !")
    return True

if __name__ == "__main__":
    success = test_text_processor()
    sys.exit(0 if success else 1)