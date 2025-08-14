"""
Processeur de texte pour chunking intelligent
Optimisé pour les documents juridiques français
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import spacy

@dataclass
class TextChunk:
    """Structure pour stocker un chunk de texte avec métadonnées"""
    text: str
    chunk_index: int
    word_count: int
    char_count: int
    chunk_type: str  # 'title', 'content', 'list_item'
    keywords: List[str]
    metadata: Dict
    
    def __post_init__(self):
        if not self.word_count:
            self.word_count = len(self.text.split())
        if not self.char_count:
            self.char_count = len(self.text)

class TextProcessor:
    """
    Processeur intelligent pour documents juridiques/RH français
    
    Analogie : Expert qui sait comment découper des textes juridiques
    en respectant la logique et le sens des documents
    """
    
    def __init__(self, chunk_size: int = 300, overlap: int = 50):
        """
        Initialise le processeur de texte
        
        Args:
            chunk_size: Taille cible en caractères (300 = optimal pour embeddings)
            overlap: Chevauchement entre chunks en caractères (50 = 15-20% overlap)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = 100  # Chunks trop petits ignorés
        
        # Configuration logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Patterns pour détecter les structures de documents juridiques
        self.section_patterns = [
            r'^[A-Z][^.]*:$',                    # "SECTION MAJEURE:"
            r'^\d+\.\s+[A-Z]',                   # "1. Titre section"
            r'^[A-Z]{2,}',                       # "TITRE EN MAJUSCULES"
            r'^\s*-\s+[A-Z]',                    # "- Point important"
            r'Article\s+\d+',                    # "Article 123"
            r'Chapitre\s+[IVX]+',                # "Chapitre II"
        ]
        
        # Mots-clés pour classification fine des chunks
        self.chunk_keywords = {
            'procedure': ['démarche', 'procédure', 'étape', 'comment', 'mode d\'emploi'],
            'definition': ['définition', 'qu\'est-ce', 'signifie', 'correspond'],
            'obligation': ['obligation', 'devoir', 'doit', 'tenu de', 'obligatoire'],
            'droit': ['droit', 'peut', 'autorisé', 'possibilité', 'faculté'],
            'sanction': ['sanction', 'amende', 'pénalité', 'infraction', 'contravention'],
            'aide': ['aide', 'subvention', 'allocation', 'financement', 'soutien']
        }
        
        # Tentative de chargement spaCy pour une segmentation plus intelligente
        try:
            self.nlp = spacy.load("fr_core_news_sm")
            self.use_spacy = True
            self.logger.info("✅ spaCy français chargé pour segmentation avancée")
        except OSError:
            self.nlp = None
            self.use_spacy = False
            self.logger.warning("⚠️ spaCy non disponible - segmentation basique utilisée")
            self.logger.info("💡 Pour installer: pip install spacy && python -m spacy download fr_core_news_sm")
    
    def clean_text(self, text: str) -> str:
        """
        Nettoie le texte avant chunking
        
        Analogie : Comme corriger et reformater un document avant l'archivage
        
        Args:
            text: Texte brut à nettoyer
            
        Returns:
            Texte nettoyé et normalisé
        """
        if not text:
            return ""
        
        # Normaliser les espaces et retours à la ligne
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Nettoyer les caractères problématiques
        text = text.replace('\u00a0', ' ')  # Espaces insécables
        text = text.replace('\u2019', "'")   # Apostrophes typographiques
        text = text.replace('\u2013', '-')   # Tirets moyens
        text = text.replace('\u2014', '-')   # Tirets longs
        
        # Normaliser la ponctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)  # Espaces avant ponctuation
        text = re.sub(r'([,.!?;:])\s*', r'\1 ', text)  # Espaces après ponctuation
        
        return text.strip()
    
    def detect_sections(self, text: str) -> List[Tuple[int, str]]:
        """
        Détecte les sections et titres dans le texte
        
        Analogie : Comme identifier les chapitres et sous-titres d'un livre
        
        Args:
            text: Texte à analyser
            
        Returns:
            Liste de (position, type_section)
        """
        sections = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Détecter les différents types de sections
            for pattern in self.section_patterns:
                if re.match(pattern, line_stripped):
                    sections.append((i, 'section_header'))
                    break
            
            # Détecter les listes à puces
            if re.match(r'^\s*[-•*]\s+', line_stripped):
                sections.append((i, 'list_item'))
            
            # Détecter les paragraphes courts (potentiels titres)
            if len(line_stripped) < 100 and line_stripped.endswith(':'):
                sections.append((i, 'subsection'))
        
        return sections
    
    def smart_split_sentences(self, text: str) -> List[str]:
        """
        Segmentation intelligente en phrases
        
        Analogie : Comme identifier où s'arrêtent vraiment les idées complètes
        
        Args:
            text: Texte à segmenter
            
        Returns:
            Liste des phrases
        """
        if self.use_spacy:
            # Segmentation avancée avec spaCy
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        else:
            # Segmentation basique par regex
            # Attention aux abréviations françaises courantes
            text = re.sub(r'\b(M|Mme|Dr|etc|cf|ex|art|vol|n°)\.\s', r'\1<!ABBREV!> ', text)
            sentences = re.split(r'[.!?]+\s+', text)
            sentences = [s.replace('<!ABBREV!>', '.').strip() for s in sentences if s.strip()]
        
        return sentences
    
    def classify_chunk_content(self, text: str) -> List[str]:
        """
        Classifie le contenu d'un chunk par mots-clés
        
        Analogie : Comme mettre des étiquettes de couleur sur des dossiers
        
        Args:
            text: Texte du chunk
            
        Returns:
            Liste des catégories détectées
        """
        text_lower = text.lower()
        detected_categories = []
        
        for category, keywords in self.chunk_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_categories.append(category)
        
        return detected_categories or ['general']
    
    def create_chunks_with_overlap(self, sentences: List[str]) -> List[TextChunk]:
        """
        Crée des chunks avec chevauchement intelligent
        
        Analogie : Comme découper un rouleau de papier avec des marques
        de repère qui se chevauchent
        
        Args:
            sentences: Liste des phrases
            
        Returns:
            Liste des chunks créés
        """
        chunks = []
        current_chunk = ""
        chunk_index = 0
        overlap_buffer = ""
        
        for i, sentence in enumerate(sentences):
            # Essayer d'ajouter la phrase au chunk actuel
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            # Si le chunk devient trop grand, finaliser le chunk actuel
            if len(potential_chunk) > self.chunk_size and current_chunk:
                # Finaliser le chunk actuel
                chunk_text = (overlap_buffer + " " + current_chunk).strip()
                
                if len(chunk_text) >= self.min_chunk_size:
                    # Créer le chunk avec métadonnées
                    keywords = self.classify_chunk_content(chunk_text)
                    
                    chunk = TextChunk(
                        text=chunk_text,
                        chunk_index=chunk_index,
                        word_count=len(chunk_text.split()),
                        char_count=len(chunk_text),
                        chunk_type='content',
                        keywords=keywords,
                        metadata={
                            'sentence_count': chunk_text.count('.') + chunk_text.count('!') + chunk_text.count('?'),
                            'has_numbers': bool(re.search(r'\d', chunk_text)),
                            'has_dates': bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', chunk_text)),
                            'complexity': 'high' if len(chunk_text.split()) > 50 else 'normal'
                        }
                    )
                    
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Préparer l'overlap pour le chunk suivant
                words = current_chunk.split()
                if len(words) > 10:  # Assez de mots pour créer un overlap
                    overlap_words = words[-int(self.overlap/10):]  # ~10 chars par mot
                    overlap_buffer = " ".join(overlap_words)
                else:
                    overlap_buffer = current_chunk
                
                # Commencer nouveau chunk
                current_chunk = sentence
            else:
                current_chunk = potential_chunk
        
        # Traiter le dernier chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            final_chunk_text = (overlap_buffer + " " + current_chunk).strip()
            keywords = self.classify_chunk_content(final_chunk_text)
            
            chunk = TextChunk(
                text=final_chunk_text,
                chunk_index=chunk_index,
                word_count=len(final_chunk_text.split()),
                char_count=len(final_chunk_text),
                chunk_type='content',
                keywords=keywords,
                metadata={
                    'sentence_count': final_chunk_text.count('.') + final_chunk_text.count('!') + final_chunk_text.count('?'),
                    'is_final': True
                }
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def process_document(self, title: str, content: str, metadata: Dict = None) -> List[TextChunk]:
        """
        Traite un document complet en chunks intelligents
        
        Méthode principale qui combine toutes les techniques
        
        Args:
            title: Titre du document
            content: Contenu du document
            metadata: Métadonnées du document source
            
        Returns:
            Liste des chunks créés
        """
        if metadata is None:
            metadata = {}
        
        self.logger.info(f"🔄 Traitement document: {title[:50]}...")
        
        # Nettoyer le texte
        clean_content = self.clean_text(content)
        
        if len(clean_content) < self.min_chunk_size:
            self.logger.warning(f"⚠️ Document trop court ({len(clean_content)} chars)")
            return []
        
        # Créer un chunk spécial pour le titre
        chunks = []
        if title and len(title.strip()) > 10:
            title_chunk = TextChunk(
                text=title.strip(),
                chunk_index=0,
                word_count=len(title.split()),
                char_count=len(title),
                chunk_type='title',
                keywords=['titre'],
                metadata={**metadata, 'is_title': True}
            )
            chunks.append(title_chunk)
        
        # Segmenter en phrases
        sentences = self.smart_split_sentences(clean_content)
        
        if not sentences:
            self.logger.warning("⚠️ Aucune phrase détectée")
            return chunks
        
        # Créer les chunks de contenu
        content_chunks = self.create_chunks_with_overlap(sentences)
        
        # Ajouter métadonnées du document source à tous les chunks
        for chunk in content_chunks:
            chunk.metadata.update(metadata)
            chunk.chunk_index += len(chunks)  # Ajuster index après titre
        
        chunks.extend(content_chunks)
        
        self.logger.info(f"✅ Document traité: {len(chunks)} chunks créés")
        self.logger.info(f"📊 Répartition: {[c.chunk_type for c in chunks]}")
        
        return chunks
    
    def get_processing_stats(self, chunks: List[TextChunk]) -> Dict:
        """
        Génère des statistiques sur le traitement
        
        Args:
            chunks: Liste des chunks traités
            
        Returns:
            Dictionnaire de statistiques
        """
        if not chunks:
            return {}
        
        total_chars = sum(c.char_count for c in chunks)
        total_words = sum(c.word_count for c in chunks)
        
        chunk_types = {}
        for chunk in chunks:
            chunk_types[chunk.chunk_type] = chunk_types.get(chunk.chunk_type, 0) + 1
        
        return {
            'total_chunks': len(chunks),
            'total_characters': total_chars,
            'total_words': total_words,
            'avg_chunk_size': total_chars // len(chunks),
            'chunk_types': chunk_types,
            'size_distribution': {
                'small': len([c for c in chunks if c.char_count < 200]),
                'medium': len([c for c in chunks if 200 <= c.char_count <= 400]),
                'large': len([c for c in chunks if c.char_count > 400])
            }
        }