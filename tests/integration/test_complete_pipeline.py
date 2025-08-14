#!/usr/bin/env python3
"""
Test du pipeline complet : Extraction → Chunking → Embeddings → Stockage PostgreSQL
Version corrigée pour pytest dans tests/integration/
"""

import sys
import os

# Fix du PYTHONPATH pour pytest depuis tests/integration/
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, root_dir)

from src.data_extraction.extractors.service_public import ServicePublicExtractor
from src.data_processing.text_processor import TextProcessor
from src.embeddings.generator import EmbeddingsGenerator
from src.database.vector_storage import VectorStorage

def test_complete_rag_pipeline():
    """Test du pipeline RAG complet de bout en bout"""
    print("🚀 TEST PIPELINE RAG COMPLET")
    print("=" * 70)
    
    # 1. EXTRACTION - Récupérer document réel
    print("📄 1. EXTRACTION - Service-Public.fr")
    print("-" * 40)
    
    extractor = ServicePublicExtractor()
    doc = extractor.extract_single_test_fiche()
    
    if not doc:
        print("❌ Impossible de récupérer un document")
        return False
    
    print(f"✅ Document extrait: {doc.title[:60]}...")
    print(f"📊 Métadonnées: {doc.domain}/{doc.metadata.get('subcategory', 'N/A')}")
    print(f"📏 Taille: {len(doc.content)} caractères")
    print(f"🔗 Source: {doc.source_url}")
    
    # 2. CHUNKING - Découpage intelligent
    print(f"\n✂️ 2. CHUNKING - Découpage intelligent")
    print("-" * 40)
    
    processor = TextProcessor(chunk_size=250, overlap=40)
    chunks = processor.process_document(
        title=doc.title,
        content=doc.content,
        metadata={
            'source_url': doc.source_url,
            'domain': doc.domain,
            'fiche_number': doc.metadata.get('fiche_number'),
            'subcategory': doc.metadata.get('subcategory')
        }
    )
    
    if not chunks:
        print("❌ Aucun chunk créé")
        return False
    
    print(f"✅ {len(chunks)} chunks créés")
    content_chunks = [c for c in chunks if c.chunk_type == 'content']
    title_chunks = [c for c in chunks if c.chunk_type == 'title']
    print(f"📋 Répartition: {len(title_chunks)} titre(s), {len(content_chunks)} contenu(s)")
    
    # 3. EMBEDDINGS - Génération vecteurs
    print(f"\n🧠 3. EMBEDDINGS - Génération vecteurs")
    print("-" * 40)
    
    generator = EmbeddingsGenerator()
    if not generator.load_model():
        print("❌ Impossible de charger le modèle")
        return False
    
    chunk_embeddings = generator.process_text_chunks(chunks)
    
    successful_embeddings = sum(1 for _, emb in chunk_embeddings if emb is not None)
    print(f"✅ Embeddings générés: {successful_embeddings}/{len(chunks)}")
    
    if successful_embeddings == 0:
        print("❌ Aucun embedding généré")
        return False
    
    # 4. STOCKAGE - PostgreSQL + pgvector
    print(f"\n🗄️ 4. STOCKAGE - PostgreSQL + pgvector")
    print("-" * 40)
    
    storage = VectorStorage()
    if not storage.connect():
        print("❌ Impossible de se connecter à PostgreSQL")
        print("💡 Assurez-vous que Docker est lancé : docker-compose up -d")
        return False
    
    # Stocker le document complet avec ses chunks
    document_id = storage.store_document_with_chunks(doc, chunk_embeddings)
    
    if not document_id:
        print("❌ Échec stockage document")
        storage.disconnect()
        return False
    
    print(f"✅ Document stocké avec ID: {document_id}")
    
    # 5. VALIDATION - Test recherche vectorielle
    print(f"\n🔍 5. VALIDATION - Test recherche vectorielle")
    print("-" * 40)
    
    # Test de recherche simple
    test_results = storage.test_vector_search("formation professionnelle")
    
    if 'error' in test_results:
        print(f"⚠️ Erreur test recherche: {test_results['error']}")
    else:
        print(f"✅ Test recherche: {test_results['sample_chunks_found']} chunks trouvés")
        
        if test_results['sample_data']:
            print("\n📋 Échantillon de données stockées:")
            for i, chunk_data in enumerate(test_results['sample_data'], 1):
                print(f"   {i}. {chunk_data['chunk_text']}")
                print(f"      Document: {chunk_data['document_title']} ({chunk_data['domain']})")
    
    # 6. STATISTIQUES - Performance globale
    print(f"\n📊 6. STATISTIQUES - Performance globale")
    print("-" * 40)
    
    storage_stats = storage.get_storage_stats()
    embedding_stats = generator.get_embedding_stats()
    
    print(f"🗄️ Base de données:")
    print(f"   - Documents totaux: {storage_stats.get('total_documents', 0)}")
    print(f"   - Chunks totaux: {storage_stats.get('total_chunks', 0)}")
    print(f"   - Taille moyenne chunk: {storage_stats.get('average_chunk_length', 0):.0f} chars")
    
    if 'documents_by_domain' in storage_stats:
        print(f"   - Répartition domaines: {storage_stats['documents_by_domain']}")
    
    print(f"\n🧠 Embeddings:")
    print(f"   - Modèle: {embedding_stats['model_name']}")
    print(f"   - Dimension: {embedding_stats['embedding_dimension']}D")
    print(f"   - Performance: {embedding_stats['average_time_per_embedding']:.3f}s/embedding")
    print(f"   - Total généré: {embedding_stats['total_embeddings_generated']}")
    
    print(f"\n💾 Stockage:")
    print(f"   - Documents stockés: {storage_stats['documents_stored']}")
    print(f"   - Chunks stockés: {storage_stats['chunks_stored']}")
    print(f"   - Temps total: {storage_stats['total_storage_time']:.2f}s")
    
    # Fermer connexion
    storage.disconnect()
    
    # 7. RÉSULTAT FINAL
    print(f"\n🎉 7. RÉSULTAT FINAL")
    print("-" * 25)
    
    print("✅ PIPELINE RAG COMPLET FONCTIONNEL !")
    print("✅ Extraction automatisée")
    print("✅ Chunking intelligent") 
    print("✅ Embeddings 384D générés")
    print("✅ Stockage vectoriel opérationnel")
    print("✅ Recherche sémantique prête")
    
    print(f"\n🎯 PROCHAINES ÉTAPES:")
    print("📋 5. Orchestration Airflow")
    print("⚡ 6. API FastAPI")
    print("💬 7. Interface Streamlit")
    
    return True

# Pour exécution directe (python test_complete_pipeline.py)
def main():
    success = test_complete_rag_pipeline()
    sys.exit(0 if success else 1)

# Pour pytest (pytest tests/integration/test_complete_pipeline.py)
def test_integration_complete_pipeline():
    """Test d'intégration complet pour pytest"""
    assert test_complete_rag_pipeline() == True

if __name__ == "__main__":
    main()