"""
Extracteur spécialisé pour Service-Public.fr
Focus sur les fiches pratiques entreprises - Version complète
"""

import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin
import time

from .base_extractor import BaseExtractor, ExtractedDocument

class ServicePublicExtractor(BaseExtractor):
    """
    Extracteur spécialisé pour entreprendre.service-public.fr
    
    Analogie : Expert en droit français qui sait exactement 
    où trouver les informations officielles sur le nouveau site
    """
    
    def __init__(self, delay: float = 2.0):
        """
        Initialise l'extracteur Service-Public
        
        Args:
            delay: Délai entre requêtes (2s = respectueux pour site gouvernemental)
        """
        super().__init__('https://entreprendre.service-public.fr', delay)
        
        # URLs de départ pour l'exploration (nouvelle structure 2025)
        self.start_urls = [
            'https://entreprendre.service-public.fr/vosdroits',
            'https://entreprendre.service-public.fr/actualites'
        ]
        
        # Pattern pour identifier les fiches pratiques
        # Format: /vosdroits/N + nombre (ex: N24267) ou /vosdroits/F + nombre
        self.fiche_pattern = re.compile(
            r'https://entreprendre\.service-public\.fr/vosdroits/[NF]\d+'
        )
        
        # Classification hiérarchique pour entreprises
        self.classification_keywords = {
            'creation_entreprise': {
                'keywords': ['création', 'créer', 'SARL', 'SAS', 'micro-entreprise', 'auto-entrepreneur', 
                           'société', 'statut', 'immatriculation', 'capital', 'gérant'],
                'domain': 'juridique'
            },
            'fiscal_entreprise': {
                'keywords': ['TVA', 'impôt', 'fiscal', 'déclaration', 'bénéfice', 'déduction', 
                           'crédit d\'impôt', 'comptabilité', 'bilan'],
                'domain': 'economique'
            },
            'droit_travail': {
                'keywords': ['salarié', 'contrat de travail', 'licenciement', 'préavis', 'indemnité',
                           'temps de travail', 'congés', 'formation professionnelle'],
                'domain': 'rh'
            },
            'social_paie': {
                'keywords': ['cotisations', 'URSSAF', 'charges sociales', 'bulletin de paie',
                           'sécurité sociale', 'retraite', 'chômage'],
                'domain': 'rh'
            },
            'aides_publiques': {
                'keywords': ['aide', 'subvention', 'crédit', 'financement', 'dispositif',
                           'accompagnement', 'soutien'],
                'domain': 'economique'
            }
        }
    
    def discover_fiche_urls(self, max_pages: int = 5) -> List[str]:
        """
        Découvre les URLs des fiches pratiques entreprises
        
        Analogie : Comme parcourir l'index d'un manuel juridique 
        pour trouver tous les chapitres pertinents
        
        Args:
            max_pages: Nombre maximum de pages d'index à explorer
            
        Returns:
            Liste des URLs de fiches pratiques
        """
        discovered_urls = set()
        
        self.logger.info("🔍 Découverte des fiches pratiques...")
        
        for start_url in self.start_urls:
            self.logger.info(f"📄 Exploration de {start_url}")
            
            soup = self.get_page(start_url)
            if not soup:
                continue
            
            # Extraire tous les liens de la page
            links = self.extract_links(soup, start_url)
            
            # Filtrer seulement les fiches pratiques
            fiche_links = [
                link for link in links 
                if self.fiche_pattern.match(link)
            ]
            
            discovered_urls.update(fiche_links)
            self.logger.info(f"✅ {len(fiche_links)} fiches trouvées sur cette page")
            
            # Limiter le nombre de fiches pour le test
            if len(discovered_urls) >= max_pages * 10:  # ~10 fiches par page
                break
        
        fiche_list = list(discovered_urls)[:max_pages * 10]
        self.logger.info(f"🎯 Total : {len(fiche_list)} fiches pratiques découvertes")
        
        return fiche_list
    
    def extract_fiche_content(self, soup) -> Tuple[str, str]:
        """
        Extrait le contenu spécifique d'une fiche pratique
        
        Analogie : Comme lire seulement le texte principal d'un article 
        de journal, en ignorant les publicités et menus
        
        Args:
            soup: Page parsée
            
        Returns:
            tuple (titre, contenu_principal)
        """
        # Extraire le titre principal
        title = ""
        title_selectors = [
            'h1.page-title',
            'h1',
            '.main-title',
            'title'
        ]
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                title = self.clean_text(title_element.get_text())
                break
        
        # Extraire le contenu principal en évitant les éléments parasites
        content_selectors = [
            '.page-content .main-content',
            '.content-main',
            '.article-content',
            '.fiche-content',
            'main'
        ]
        
        # Supprimer les éléments non-informatifs
        elements_to_remove = [
            'nav', 'header', 'footer', 'aside', '.sidebar', '.navigation',
            '.breadcrumb', '.social-share', '.print-link', '.search-form',
            '.advertisement', '.pub', '.banner', '.menu'
        ]
        
        for selector in elements_to_remove:
            for element in soup.select(selector):
                element.decompose()
        
        # Extraire le contenu principal
        content = ""
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                content = self.clean_text(content_element.get_text())
                break
        
        # Si pas de sélecteur spécifique, prendre le body sans navigation
        if not content or len(content) < 200:
            content = self.extract_text_content(soup)
        
        return title, content
    
    def classify_fiche_domain(self, title: str, content: str, url: str) -> Tuple[str, str]:
        """
        Classification hiérarchique spécialisée pour fiches service-public
        
        Analogie : Expert qui lit un document et dit précisément :
        "C'est du droit commercial, sous-catégorie création d'entreprise"
        
        Args:
            title: Titre de la fiche
            content: Contenu de la fiche
            url: URL source
            
        Returns:
            tuple (domaine_principal, sous_categorie)
        """
        text_to_analyze = (title + " " + content[:1000]).lower()
        
        # Scores par sous-catégorie
        subcategory_scores = {}
        
        for subcategory, config in self.classification_keywords.items():
            score = sum(
                1 for keyword in config['keywords'] 
                if keyword.lower() in text_to_analyze
            )
            if score > 0:
                subcategory_scores[subcategory] = {
                    'score': score,
                    'domain': config['domain']
                }
        
        # Retourner la meilleure classification
        if subcategory_scores:
            best_subcategory = max(subcategory_scores, key=lambda x: subcategory_scores[x]['score'])
            main_domain = subcategory_scores[best_subcategory]['domain']
            
            self.logger.info(f"🏷️ Classification: {main_domain} > {best_subcategory}")
            return main_domain, best_subcategory
        else:
            return 'juridique', 'general'  # Défaut pour service-public.fr
    
    def extract_fiche(self, url: str) -> Optional[ExtractedDocument]:
        """
        Extrait une fiche pratique complète
        
        Méthode principale optimisée pour entreprendre.service-public.fr
        
        Args:
            url: URL de la fiche pratique
            
        Returns:
            ExtractedDocument enrichi ou None
        """
        # Vérifier que c'est bien une fiche pratique
        if not self.fiche_pattern.match(url):
            self.logger.warning(f"⚠️ URL non-conforme : {url}")
            return None
        
        # Récupérer la page
        soup = self.get_page(url)
        if not soup:
            return None
        
        # Extraire titre et contenu spécialisés
        title, content = self.extract_fiche_content(soup)
        
        if len(content) < 200:  # Seuil minimal pour une fiche pratique
            self.logger.warning(f"⚠️ Contenu insuffisant pour {url}")
            return None
        
        # Classification hiérarchique
        main_domain, subcategory = self.classify_fiche_domain(title, content, url)
        
        # Extraire métadonnées supplémentaires
        metadata = {
            'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'content_length': len(content),
            'title_length': len(title),
            'source_type': 'fiche_pratique',
            'subcategory': subcategory,
            'url_pattern': 'entreprendre_service_public'
        }
        
        # Ajouter numéro de fiche si disponible (N ou F + nombre)
        fiche_match = re.search(r'/([NF]\d+)$', url)
        if fiche_match:
            metadata['fiche_number'] = fiche_match.group(1)
        
        document = ExtractedDocument(
            title=title,
            content=content,
            source_url=url,
            domain=main_domain,
            metadata=metadata
        )
        
        self.logger.info(
            f"✅ Fiche extraite: {title[:50]}... "
            f"({main_domain}/{subcategory}, {len(content)} chars)"
        )
        
        return document
    
    def extract_multiple_fiches(self, max_fiches: int = 20) -> List[ExtractedDocument]:
        """
        Extrait plusieurs fiches pratiques en lot
        
        Analogie : Comme demander à un stagiaire de préparer 
        un dossier complet sur 20 sujets juridiques différents
        
        Args:
            max_fiches: Nombre maximum de fiches à extraire
            
        Returns:
            Liste des documents extraits
        """
        self.logger.info(f"🚀 EXTRACTION EN LOT - {max_fiches} fiches maximum")
        
        # Découvrir les URLs
        fiche_urls = self.discover_fiche_urls(max_pages=3)
        
        if not fiche_urls:
            self.logger.error("❌ Aucune fiche découverte")
            return []
        
        # Limiter au nombre demandé
        fiche_urls = fiche_urls[:max_fiches]
        
        # Extraire chaque fiche
        extracted_docs = []
        
        for i, url in enumerate(fiche_urls, 1):
            self.logger.info(f"📄 Fiche {i}/{len(fiche_urls)}: {url}")
            
            doc = self.extract_fiche(url)
            if doc:
                extracted_docs.append(doc)
            
            # Pause respectueuse entre extractions
            if i < len(fiche_urls):
                time.sleep(self.delay)
        
        self.logger.info(f"🎉 EXTRACTION TERMINÉE: {len(extracted_docs)} fiches extraites avec succès")
        
        # Statistiques par domaine
        domain_stats = {}
        for doc in extracted_docs:
            domain = doc.domain
            domain_stats[domain] = domain_stats.get(domain, 0) + 1
        
        self.logger.info("📊 Répartition par domaine:")
        for domain, count in domain_stats.items():
            self.logger.info(f"   - {domain}: {count} fiches")
        
        return extracted_docs
    
    def extract_single_test_fiche(self, test_url: str = None) -> Optional[ExtractedDocument]:
        """
        Méthode de test pour extraire une seule fiche
        
        Args:
            test_url: URL spécifique à tester (défaut: N24267)
            
        Returns:
            Document extrait ou None
        """
        if test_url is None:
            test_url = "https://entreprendre.service-public.fr/vosdroits/N24267"
        
        self.logger.info(f"🧪 Test extraction fiche: {test_url}")
        
        return self.extract_fiche(test_url)