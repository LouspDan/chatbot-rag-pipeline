"""
Module de stockage vectoriel pour PostgreSQL + pgvector
Intégration chunks + embeddings dans la base de données
"""

import logging
import time
from typing import List, Dict, Optional, Tuple, Union
import psycopg2
import psycopg2.extras
import numpy as np
from dataclasses import asdict

from ..data_processing.text_processor import TextChunk
from ..data_extraction.extractors.base_extractor import ExtractedDocument

class VectorStorage:
    """
    Gestionnaire de stockage vectoriel pour PostgreSQL + pgvector
    
    Analogie : Bibliothécaire ultra-efficace qui range et retrouve 
    instantanément des documents par leur "signature numérique"
    """
    
    def __init__(self, db_config: Dict = None):
        """
        Initialise la connexion au stockage vectoriel
        
        Args:
            db_config: Configuration base de données
        """
        # Configuration par défaut (même que nos tests précédents)
        self.db_config = db_config or {
            'host': 'localhost',
            'port': 5432,
            'database': 'chatbot_db',
            'user': 'chatbot_user',
            'password': 'chatbot_password'
        }
        
        self.connection = None
        
        # Configuration logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Statistiques de performance
        self.stats = {
            'documents_stored': 0,
            'chunks_stored': 0,
            'total_storage_time': 0.0,
            'last_operation_time': None
        }
    
    def connect(self) -> bool:
        """
        Établit la connexion à PostgreSQL
        
        Returns:
            True si connexion réussie, False sinon
        """
        try:
            self.logger.info("🔄 Connexion à PostgreSQL...")
            
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = False  # Transactions manuelles
            
            # Test de la connexion et vérification pgvector
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.logger.info(f"✅ PostgreSQL connecté: {version[:50]}...")
                
                # Vérifier l'extension pgvector
                cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
                extension = cursor.fetchone()
                if extension:
                    self.logger.info("✅ Extension pgvector détectée")
                else:
                    self.logger.error("❌ Extension pgvector manquante")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur connexion PostgreSQL: {e}")
            return False
    
    def disconnect(self):
        """Ferme la connexion à la base de données"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("✅ Connexion PostgreSQL fermée")
    
    def store_document(self, document: ExtractedDocument) -> Optional[int]:
        """
        Stocke un document dans la table documents
        
        Args:
            document: Document extrait à stocker
            
        Returns:
            ID du document inséré ou None si erreur
        """
        if not self.connection:
            self.logger.error("❌ Pas de connexion à la base")
            return None
        
        try:
            with self.connection.cursor() as cursor:
                # Insérer le document
                insert_query = """
                    INSERT INTO documents (title, source_url, content, domain, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id
                """
                
                cursor.execute(insert_query, (
                    document.title,
                    document.source_url,
                    document.content,
                    document.domain
                ))
                
                document_id = cursor.fetchone()[0]
                self.connection.commit()
                
                self.stats['documents_stored'] += 1
                self.logger.info(f"✅ Document stocké: ID {document_id}")
                
                return document_id
                
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"❌ Erreur stockage document: {e}")
            return None
    
    def store_chunk_with_embedding(self, 
                                 document_id: int, 
                                 chunk: TextChunk, 
                                 embedding: np.ndarray) -> Optional[int]:
        """
        Stocke un chunk avec son embedding vectoriel
        
        Args:
            document_id: ID du document parent
            chunk: Chunk de texte
            embedding: Vecteur embedding correspondant
            
        Returns:
            ID du chunk inséré ou None si erreur
        """
        if not self.connection:
            self.logger.error("❌ Pas de connexion à la base")
            return None
        
        if embedding is None:
            self.logger.warning("⚠️ Embedding None ignoré")
            return None
        
        try:
            with self.connection.cursor() as cursor:
                # Convertir l'embedding en format pgvector
                embedding_list = embedding.tolist()
                
                # Insérer le chunk avec son embedding
                insert_query = """
                    INSERT INTO text_chunks (
                        document_id, chunk_text, chunk_index, embedding, created_at
                    ) VALUES (%s, %s, %s, %s::vector, CURRENT_TIMESTAMP)
                    RETURNING id
                """
                
                cursor.execute(insert_query, (
                    document_id,
                    chunk.text,
                    chunk.chunk_index,
                    embedding_list
                ))
                
                chunk_id = cursor.fetchone()[0]
                self.connection.commit()
                
                self.stats['chunks_stored'] += 1
                self.logger.debug(f"✅ Chunk stocké: ID {chunk_id}")
                
                return chunk_id
                
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"❌ Erreur stockage chunk: {e}")
            return None
    
    def store_document_with_chunks(self, 
                                 document: ExtractedDocument,
                                 chunk_embeddings: List[Tuple[TextChunk, Optional[np.ndarray]]]) -> Optional[int]:
        """
        Stocke un document complet avec tous ses chunks et embeddings
        
        Méthode principale pour notre pipeline
        
        Args:
            document: Document source
            chunk_embeddings: Liste de (chunk, embedding)
            
        Returns:
            ID du document stocké ou None si erreur
        """
        if not chunk_embeddings:
            self.logger.warning("⚠️ Aucun chunk à stocker")
            return None
        
        start_time = time.time()
        self.logger.info(f"🔄 Stockage document complet: {document.title[:50]}...")
        
        try:
            # 1. Stocker le document principal
            document_id = self.store_document(document)
            if not document_id:
                return None
            
            # 2. Stocker tous les chunks avec embeddings
            stored_chunks = 0
            failed_chunks = 0
            
            for chunk, embedding in chunk_embeddings:
                if embedding is not None:
                    chunk_id = self.store_chunk_with_embedding(document_id, chunk, embedding)
                    if chunk_id:
                        stored_chunks += 1
                    else:
                        failed_chunks += 1
                else:
                    failed_chunks += 1
                    self.logger.warning(f"⚠️ Chunk sans embedding ignoré: {chunk.text[:50]}...")
            
            # 3. Statistiques finales
            storage_time = time.time() - start_time
            self.stats['total_storage_time'] += storage_time
            self.stats['last_operation_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            success_rate = (stored_chunks / len(chunk_embeddings)) * 100
            
            self.logger.info(f"✅ Stockage terminé en {storage_time:.2f}s")
            self.logger.info(f"📊 Chunks stockés: {stored_chunks}/{len(chunk_embeddings)} ({success_rate:.1f}%)")
            
            if failed_chunks > 0:
                self.logger.warning(f"⚠️ Chunks échoués: {failed_chunks}")
            
            return document_id
            
        except Exception as e:
            self.logger.error(f"❌ Erreur stockage complet: {e}")
            return None
    
    def search_similar_chunks(self, 
                            query_embedding: np.ndarray, 
                            limit: int = 5,
                            similarity_threshold: float = 0.0) -> List[Dict]:
        """
        Recherche les chunks les plus similaires à un embedding de requête
        
        Args:
            query_embedding: Vecteur de la requête
            limit: Nombre maximum de résultats
            similarity_threshold: Seuil de similarité minimum
            
        Returns:
            Liste des chunks similaires avec métadonnées
        """
        if not self.connection:
            self.logger.error("❌ Pas de connexion à la base")
            return []
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Requête de recherche vectorielle avec jointure
                search_query = """
                    SELECT 
                        tc.id as chunk_id,
                        tc.chunk_text,
                        tc.chunk_index,
                        (tc.embedding <=> %s::vector) as distance,
                        (1 - (tc.embedding <=> %s::vector)) as similarity,
                        d.id as document_id,
                        d.title as document_title,
                        d.domain,
                        d.source_url
                    FROM text_chunks tc
                    JOIN documents d ON tc.document_id = d.id
                    WHERE (1 - (tc.embedding <=> %s::vector)) >= %s
                    ORDER BY tc.embedding <=> %s::vector
                    LIMIT %s
                """
                
                query_vector = query_embedding.tolist()
                
                cursor.execute(search_query, (
                    query_vector, query_vector, query_vector, 
                    similarity_threshold, query_vector, limit
                ))
                
                results = cursor.fetchall()
                
                # Convertir en liste de dictionnaires
                similar_chunks = []
                for row in results:
                    similar_chunks.append({
                        'chunk_id': row['chunk_id'],
                        'chunk_text': row['chunk_text'],
                        'chunk_index': row['chunk_index'],
                        'similarity': float(row['similarity']),
                        'distance': float(row['distance']),
                        'document_id': row['document_id'],
                        'document_title': row['document_title'],
                        'domain': row['domain'],
                        'source_url': row['source_url']
                    })
                
                self.logger.info(f"🔍 Recherche terminée: {len(similar_chunks)} résultats")
                
                return similar_chunks
                
        except Exception as e:
            self.logger.error(f"❌ Erreur recherche vectorielle: {e}")
            return []
    
    def get_storage_stats(self) -> Dict:
        """
        Retourne les statistiques de stockage et de la base
        
        Returns:
            Dictionnaire avec les métriques
        """
        stats = dict(self.stats)
        
        if self.connection:
            try:
                with self.connection.cursor() as cursor:
                    # Compter les documents
                    cursor.execute("SELECT COUNT(*) FROM documents")
                    stats['total_documents'] = cursor.fetchone()[0]
                    
                    # Compter les chunks
                    cursor.execute("SELECT COUNT(*) FROM text_chunks")
                    stats['total_chunks'] = cursor.fetchone()[0]
                    
                    # Compter par domaine
                    cursor.execute("""
                        SELECT domain, COUNT(*) 
                        FROM documents 
                        GROUP BY domain 
                        ORDER BY COUNT(*) DESC
                    """)
                    stats['documents_by_domain'] = dict(cursor.fetchall())
                    
                    # Taille moyenne des chunks
                    cursor.execute("SELECT AVG(LENGTH(chunk_text)) FROM text_chunks")
                    avg_length = cursor.fetchone()[0]
                    stats['average_chunk_length'] = float(avg_length) if avg_length else 0
                    
            except Exception as e:
                self.logger.error(f"⚠️ Erreur récupération stats: {e}")
        
        return stats
    
    def test_vector_search(self, test_query: str = "formation professionnelle") -> Dict:
        """
        Test de la recherche vectorielle avec une requête simple
        
        Args:
            test_query: Texte de test pour la recherche
            
        Returns:
            Résultats du test
        """
        if not self.connection:
            return {"error": "Pas de connexion à la base"}
        
        # Pour ce test, on va créer un embedding simple de la requête
        # (nécessiterait normalement le générateur d'embeddings)
        try:
            with self.connection.cursor() as cursor:
                # Test basique : récupérer quelques chunks existants
                cursor.execute("""
                    SELECT tc.chunk_text, d.title, d.domain
                    FROM text_chunks tc
                    JOIN documents d ON tc.document_id = d.id
                    LIMIT 3
                """)
                
                sample_chunks = cursor.fetchall()
                
                return {
                    "test_query": test_query,
                    "sample_chunks_found": len(sample_chunks),
                    "sample_data": [
                        {
                            "chunk_text": chunk[0][:100] + "...",
                            "document_title": chunk[1][:50] + "...",
                            "domain": chunk[2]
                        }
                        for chunk in sample_chunks
                    ]
                }
                
        except Exception as e:
            return {"error": f"Erreur test: {e}"}