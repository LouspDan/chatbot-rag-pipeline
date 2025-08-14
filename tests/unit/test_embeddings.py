#!/usr/bin/env python3
"""
Test du générateur d'embeddings avec nos chunks réels
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_extraction.extractors.service_public import ServicePublicExtractor
from src.data_processing.text_processor import TextProcessor
from src.embeddings.generator import EmbeddingsGenerator

def test_embeddings_pipeline():
    """Test complet : Extraction → Chunking → Embeddings"""
    print("🧪 TEST PIPELINE EMBEDDINGS COMPLET")
    print("=" * 60)
    
    # 1. Récupérer un document réel
    print("📄 1. Extraction document Service-Public...")
    extractor = ServicePublicExtractor()
    doc = extractor.extract_single_test_fiche()
    
    if not doc:
        print("❌ Impossible de récupérer un document test")
        return False
    
    print(f"✅ Document récupéré: {doc.title[:50]}...")
    print(f"📊 Longueur: {len(doc.content)} caractères")
    
    # 2. Chunking intelligent
    print("\n🔄 2. Chunking intelligent...")
    processor = TextProcessor(chunk_size=250, overlap=40)
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
    
    # 3. Génération embeddings
    print("\n🧠 3. Génération embeddings...")
    generator = EmbeddingsGenerator()
    
    # Charger le modèle
    if not generator.load_model():
        print("❌ Impossible de charger le modèle")
        return False
    
    # Traiter les chunks
    chunk_embeddings = generator.process_text_chunks(chunks)
    
    print(f"✅ {len(chunk_embeddings)} chunks traités")
    
    # 4. Analyser les résultats
    print("\n📋 4. ANALYSE DES EMBEDDINGS:")
    print("-" * 50)
    
    successful_embeddings = 0
    for i, (chunk, embedding) in enumerate(chunk_embeddings):
        status = "✅" if embedding is not None else "❌"
        embedding_info = f"Vector({len(embedding)}D)" if embedding is not None else "Failed"
        
        print(f"{status} Chunk {i+1} ({chunk.chunk_type}):")
        print(f"   📝 Texte: {chunk.text[:80]}...")
        print(f"   🔢 Embedding: {embedding_info}")
        print(f"   🏷️ Mots-clés: {', '.join(chunk.keywords)}")
        
        if embedding is not None:
            successful_embeddings += 1
            # Afficher quelques valeurs d'exemple
            sample_values = embedding[:5]
            print(f"   📊 Échantillon: [{', '.join([f'{v:.3f}' for v in sample_values])}...]")
        print()
    
    # 5. Statistiques globales
    print("📊 5. STATISTIQUES EMBEDDINGS:")
    print("-" * 40)
    
    stats = generator.get_embedding_stats()
    success_rate = (successful_embeddings / len(chunks)) * 100
    
    print(f"🎯 Modèle: {stats['model_name']}")
    print(f"📐 Dimension: {stats['embedding_dimension']}D")
    print(f"✅ Succès: {successful_embeddings}/{len(chunks)} ({success_rate:.1f}%)")
    print(f"⚡ Performance: {stats['average_time_per_embedding']:.3f}s/embedding")
    print(f"📈 Total généré: {stats['total_embeddings_generated']}")
    
    # 6. Test de qualité des embeddings
    print("\n🧪 6. TEST QUALITÉ EMBEDDINGS:")
    print("-" * 35)
    
    quality_test = generator.test_embedding_quality([
        "formation professionnelle salarié",
        "droit du travail employé", 
        "cotisations sociales URSSAF",
        "création entreprise SARL"
    ])
    
    if 'error' not in quality_test:
        print(f"📊 Tests réalisés: {quality_test['test_texts_count']}")
        print(f"📐 Dimension confirmée: {quality_test['embedding_dimension']}D")
        print(f"📈 Similarité moyenne: {quality_test['average_similarity']:.3f}")
        
        print("\n🏆 Top 3 similarités:")
        for i, sim in enumerate(quality_test['top_similarities'], 1):
            print(f"   {i}. {sim['similarity']:.3f} - \"{sim['text1']}\" ↔ \"{sim['text2']}\"")
    else:
        print(f"⚠️ Erreur test qualité: {quality_test['error']}")
    
    # 7. Validation finale
    print(f"\n🎉 PIPELINE EMBEDDINGS COMPLET TESTÉ !")
    print("-" * 45)
    
    if successful_embeddings >= len(chunks) * 0.8:  # 80% de succès minimum
        print("✅ Pipeline embeddings fonctionnel")
        print("✅ Prêt pour intégration base vectorielle")
        return True
    else:
        print("⚠️ Taux de succès embeddings insuffisant")
        return False

if __name__ == "__main__":
    success = test_embeddings_pipeline()
    sys.exit(0 if success else 1)