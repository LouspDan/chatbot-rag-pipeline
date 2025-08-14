"""
Générateur d'embeddings pour chunks de texte
Optimisé pour le français juridique/RH
"""

import logging
import time
from typing import List, Dict, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer

from ..data_processing.text_processor import TextChunk

class EmbeddingsGenerator:
    """
    Générateur d'embeddings spécialisé pour textes juridiques français
    
    Analogie : Traducteur qui convertit des phrases françaises 
    en "codes numériques" que l'ordinateur comprend
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialise le générateur d'embeddings
        
        Args:
            model_name: Nom du modèle à utiliser
                       - all-MiniLM-L6-v2: Rapide, 384 dims, bon pour usage général
                       - paraphrase-multilingual: Meilleur pour français mais plus lourd
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dimension = None
        
        # Configuration logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Statistiques de performance
        self.stats = {
            'total_embeddings_generated': 0,
            'total_processing_time': 0.0,
            'average_time_per_embedding': 0.0,
            'model_loaded_at': None
        }
        
        # Configuration pour optimisation batch
        self.batch_size = 32  # Traiter par lots pour performance
        
    def load_model(self) -> bool:
        """
        Charge le modèle d'embeddings
        
        Analogie : Comme charger un dictionnaire spécialisé 
        dans la mémoire avant de commencer à traduire
        
        Returns:
            True si chargement réussi, False sinon
        """
        try:
            self.logger.info(f"🔄 Chargement du modèle {self.model_name}...")
            start_time = time.time()
            
            # Charger le modèle sentence-transformers
            self.model = SentenceTransformer(self.model_name)
            
            # Déterminer la dimension des embeddings
            test_embedding = self.model.encode(["test"])
            self.embedding_dimension = test_embedding.shape[1]
            
            load_time = time.time() - start_time
            self.stats['model_loaded_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            self.logger.info(f"✅ Modèle chargé en {load_time:.2f}s")
            self.logger.info(f"📊 Dimension embeddings: {self.embedding_dimension}")
            self.logger.info(f"🎯 Modèle optimisé pour: {self._get_model_info()}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement modèle: {e}")
            return False
    
    def _get_model_info(self) -> str:
        """Retourne des infos sur le modèle utilisé"""
        model_infos = {
            "all-MiniLM-L6-v2": "Usage général, rapide, 384 dimensions",
            "paraphrase-multilingual-MiniLM-L12-v2": "Multilingue, français optimisé",
            "distiluse-base-multilingual-cased": "Multilingue, bonne qualité"
        }
        
        for model_key, info in model_infos.items():
            if model_key in self.model_name:
                return info
        
        return "Modèle personnalisé"
    
    def preprocess_text_for_embedding(self, text: str) -> str:
        """
        Préprocesse le texte avant génération embedding
        
        Analogie : Comme nettoyer et formater un texte 
        avant de le soumettre à un traducteur
        
        Args:
            text: Texte brut à préprocesser
            
        Returns:
            Texte nettoyé optimisé pour embedding
        """
        if not text:
            return ""
        
        # Nettoyer le texte
        cleaned = text.strip()
        
        # Limiter la longueur (modèles ont des limites)
        max_length = 512  # Tokens approximatifs
        if len(cleaned) > max_length:
            # Couper intelligemment (éviter de couper au milieu d'un mot)
            cleaned = cleaned[:max_length]
            last_space = cleaned.rfind(' ')
            if last_space > max_length * 0.8:  # Si l'espace est assez proche
                cleaned = cleaned[:last_space]
            
            self.logger.warning(f"⚠️ Texte tronqué à {len(cleaned)} caractères")
        
        return cleaned
    
    def generate_single_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Génère un embedding pour un texte unique
        
        Args:
            text: Texte à encoder
            
        Returns:
            Array numpy de l'embedding ou None si erreur
        """
        if not self.model:
            self.logger.error("❌ Modèle non chargé")
            return None
        
        if not text or len(text.strip()) < 3:
            self.logger.warning("⚠️ Texte trop court pour embedding")
            return None
        
        try:
            start_time = time.time()
            
            # Préprocesser
            clean_text = self.preprocess_text_for_embedding(text)
            
            # Générer embedding
            embedding = self.model.encode([clean_text])
            
            # Extraire le vecteur (première dimension du batch)
            embedding_vector = embedding[0]
            
            # Statistiques
            processing_time = time.time() - start_time
            self.stats['total_embeddings_generated'] += 1
            self.stats['total_processing_time'] += processing_time
            self.stats['average_time_per_embedding'] = (
                self.stats['total_processing_time'] / 
                self.stats['total_embeddings_generated']
            )
            
            self.logger.debug(f"✅ Embedding généré en {processing_time:.3f}s")
            
            return embedding_vector
            
        except Exception as e:
            self.logger.error(f"❌ Erreur génération embedding: {e}")
            return None
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """
        Génère des embeddings en lot (plus efficace)
        
        Analogie : Traiter plusieurs phrases d'un coup 
        plutôt qu'une par une (plus rapide)
        
        Args:
            texts: Liste des textes à encoder
            
        Returns:
            Liste des embeddings (None si erreur sur un texte)
        """
        if not self.model:
            self.logger.error("❌ Modèle non chargé")
            return [None] * len(texts)
        
        if not texts:
            return []
        
        self.logger.info(f"🔄 Génération embeddings batch: {len(texts)} textes")
        
        # Préprocesser tous les textes
        clean_texts = []
        valid_indices = []
        
        for i, text in enumerate(texts):
            if text and len(text.strip()) >= 3:
                clean_texts.append(self.preprocess_text_for_embedding(text))
                valid_indices.append(i)
            else:
                self.logger.warning(f"⚠️ Texte {i} ignoré (trop court)")
        
        if not clean_texts:
            self.logger.warning("⚠️ Aucun texte valide pour embedding")
            return [None] * len(texts)
        
        try:
            start_time = time.time()
            
            # Générer embeddings en batch
            embeddings = self.model.encode(clean_texts, batch_size=self.batch_size)
            
            # Reconstituer la liste complète avec None pour textes invalides
            result_embeddings = [None] * len(texts)
            for i, valid_idx in enumerate(valid_indices):
                result_embeddings[valid_idx] = embeddings[i]
            
            # Statistiques
            processing_time = time.time() - start_time
            valid_count = len(clean_texts)
            
            self.stats['total_embeddings_generated'] += valid_count
            self.stats['total_processing_time'] += processing_time
            self.stats['average_time_per_embedding'] = (
                self.stats['total_processing_time'] / 
                self.stats['total_embeddings_generated']
            )
            
            self.logger.info(f"✅ Batch terminé: {valid_count}/{len(texts)} embeddings en {processing_time:.2f}s")
            self.logger.info(f"📊 Performance: {valid_count/processing_time:.1f} embeddings/seconde")
            
            return result_embeddings
            
        except Exception as e:
            self.logger.error(f"❌ Erreur batch embeddings: {e}")
            return [None] * len(texts)
    
    def process_text_chunks(self, chunks: List[TextChunk]) -> List[Tuple[TextChunk, Optional[np.ndarray]]]:
        """
        Traite une liste de chunks et génère leurs embeddings
        
        Méthode principale pour notre pipeline
        
        Args:
            chunks: Liste des chunks à traiter
            
        Returns:
            Liste de tuples (chunk, embedding)
        """
        if not chunks:
            return []
        
        self.logger.info(f"🎯 Traitement de {len(chunks)} chunks de texte")
        
        # Extraire les textes des chunks
        texts = [chunk.text for chunk in chunks]
        
        # Générer embeddings en batch
        embeddings = self.generate_batch_embeddings(texts)
        
        # Combiner chunks et embeddings
        results = []
        successful_embeddings = 0
        
        for chunk, embedding in zip(chunks, embeddings):
            results.append((chunk, embedding))
            if embedding is not None:
                successful_embeddings += 1
        
        success_rate = (successful_embeddings / len(chunks)) * 100
        self.logger.info(f"✅ Traitement terminé: {successful_embeddings}/{len(chunks)} embeddings générés ({success_rate:.1f}%)")
        
        return results
    
    def get_embedding_stats(self) -> Dict:
        """
        Retourne les statistiques de performance
        
        Returns:
            Dictionnaire avec les métriques de performance
        """
        return {
            **self.stats,
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dimension,
            'batch_size': self.batch_size,
            'model_loaded': self.model is not None
        }
    
    def test_embedding_quality(self, test_texts: List[str] = None) -> Dict:
        """
        Test de qualité des embeddings avec exemples
        
        Args:
            test_texts: Textes de test (utilise exemples par défaut si None)
            
        Returns:
            Résultats des tests de similarité
        """
        if test_texts is None:
            # Exemples de test pour le domaine juridique/RH français
            test_texts = [
                "création d'une SARL",
                "créer une société à responsabilité limitée",
                "licenciement économique",
                "formation professionnelle",
                "cotisations URSSAF",
                "charges sociales entreprise"
            ]
        
        if not self.model:
            return {"error": "Modèle non chargé"}
        
        self.logger.info("🧪 Test qualité embeddings...")
        
        # Générer embeddings pour tests
        embeddings = self.generate_batch_embeddings(test_texts)
        valid_embeddings = [(i, emb) for i, emb in enumerate(embeddings) if emb is not None]
        
        if len(valid_embeddings) < 2:
            return {"error": "Pas assez d'embeddings valides pour test"}
        
        # Calculer similarités
        similarities = []
        
        for i, (idx1, emb1) in enumerate(valid_embeddings):
            for j, (idx2, emb2) in enumerate(valid_embeddings[i+1:], i+1):
                # Similarité cosine
                similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                similarities.append({
                    'text1': test_texts[idx1],
                    'text2': test_texts[idx2], 
                    'similarity': float(similarity)
                })
        
        # Trier par similarité décroissante
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            'test_texts_count': len(test_texts),
            'valid_embeddings': len(valid_embeddings),
            'top_similarities': similarities[:3],  # Top 3
            'average_similarity': np.mean([s['similarity'] for s in similarities]),
            'embedding_dimension': self.embedding_dimension
        }