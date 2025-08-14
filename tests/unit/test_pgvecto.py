"""
Test de validation pgvector + embeddings
Vérifie que la recherche sémantique fonctionne
"""

import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
import json

# Configuration DB (depuis votre .env)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'chatbot_db',
    'user': 'chatbot_user',
    'password': 'chatbot_password'
}

def test_connection():
    """Test connexion PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test basique
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL connecté : {version[:50]}...")
        
        # Test extension pgvector
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        extension = cursor.fetchone()
        if extension:
            print("✅ Extension pgvector installée")
        else:
            print("❌ Extension pgvector manquante")
            return False
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur connexion : {e}")
        return False

def test_embeddings():
    """Test génération embeddings avec sentence-transformers"""
    try:
        print("🔄 Chargement modèle sentence-transformers...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Phrases de test
        sentences = [
            "Quels sont les délais de préavis en CDI ?",
            "Comment calculer les cotisations URSSAF ?",
            "Procédure de création d'une SARL",
            "Droits et obligations du salarié",
            "Déclaration de revenus d'une entreprise"
        ]
        
        # Génération embeddings
        embeddings = model.encode(sentences)
        print(f"✅ Embeddings générés : {embeddings.shape}")
        print(f"✅ Dimension : {embeddings.shape[1]}")
        
        return model, sentences, embeddings
        
    except Exception as e:
        print(f"❌ Erreur embeddings : {e}")
        return None, None, None

def test_vector_storage(model, sentences, embeddings):
    """Test stockage et recherche vectorielle"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔄 Insertion documents de test...")
        
        # Nettoyage pour test
        cursor.execute("DELETE FROM text_chunks WHERE document_id IN (SELECT id FROM documents WHERE domain = 'test_vector')")
        cursor.execute("DELETE FROM documents WHERE domain = 'test_vector'")
        
        # Insertion documents
        for i, (sentence, embedding) in enumerate(zip(sentences, embeddings)):
            # Document
            cursor.execute("""
                INSERT INTO documents (title, content, domain) 
                VALUES (%s, %s, %s) RETURNING id
            """, (f"Doc Test {i+1}", sentence, "test_vector"))
            
            doc_id = cursor.fetchone()[0]
            
            # Chunk avec embedding
            embedding_list = embedding.tolist()
            cursor.execute("""
                INSERT INTO text_chunks (document_id, chunk_text, chunk_index, embedding) 
                VALUES (%s, %s, %s, %s)
            """, (doc_id, sentence, 0, embedding_list))
        
        conn.commit()
        print("✅ Documents insérés avec embeddings")
        
        # Test recherche sémantique
        print("\n🔍 Test recherche sémantique...")
        
        query = "Préavis démission CDI"
        query_embedding = model.encode([query])[0].tolist()
        
        cursor.execute("""
            SELECT 
                d.title,
                tc.chunk_text,
                (tc.embedding <=> %s::vector) as distance
            FROM text_chunks tc
            JOIN documents d ON tc.document_id = d.id
            WHERE d.domain = 'test_vector'
            ORDER BY tc.embedding <=> %s::vector
            LIMIT 3
        """, (query_embedding, query_embedding))
        
        results = cursor.fetchall()
        
        print(f"\n📊 Résultats pour : '{query}'")
        print("-" * 60)
        for i, (title, text, distance) in enumerate(results, 1):
            similarity = 1 - distance  # Convert distance to similarity
            print(f"{i}. {title}")
            print(f"   Texte: {text}")
            print(f"   Similarité: {similarity:.3f}")
            print()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur stockage vectoriel : {e}")
        return False

def main():
    """Test complet de la stack vectorielle"""
    print("🧪 TEST PGVECTOR + EMBEDDINGS")
    print("=" * 50)
    
    # Test 1: Connexion
    if not test_connection():
        return
    
    # Test 2: Embeddings
    model, sentences, embeddings = test_embeddings()
    if model is None:
        return
    
    # Test 3: Stockage et recherche
    if test_vector_storage(model, sentences, embeddings):
        print("🎉 TOUS LES TESTS PASSÉS !")
        print("✅ Stack vectorielle opérationnelle")
        print("✅ Prêt pour le pipeline complet")
    else:
        print("❌ Échec tests vectoriels")

if __name__ == "__main__":
    main()