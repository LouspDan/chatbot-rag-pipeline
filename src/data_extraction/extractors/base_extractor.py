"""
Extracteur de base pour récupération de données web
Classe parent réutilisable pour tous les sites
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ExtractedDocument:
    """Structure pour stocker un document extrait"""
    title: str
    content: str
    source_url: str
    domain: str  # 'juridique', 'rh', 'economique'
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BaseExtractor:
    """
    Extracteur de base pour sites web
    
    Analogie : C'est comme un modèle de "stagiaire" que vous pouvez 
    former pour travailler sur différents sites web
    """
    
    def __init__(self, base_url: str, delay: float = 1.0):
        """
        Initialise l'extracteur
        
        Args:
            base_url: URL racine du site (ex: "https://service-public.fr")
            delay: Temps d'attente entre requêtes (politesse web)
        """
        self.base_url = base_url
        self.delay = delay  # Être poli avec les serveurs
        self.session = requests.Session()
        
        # Headers pour simuler un navigateur réel
        # (Certains sites bloquent les robots)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Configuration du logging pour suivre le processus
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Récupère et parse une page web
        
        Analogie : Comme ouvrir une page dans votre navigateur
        et la "lire" pour en extraire le contenu
        
        Args:
            url: L'adresse de la page à récupérer
            
        Returns:
            BeautifulSoup object ou None si erreur
        """
        try:
            self.logger.info(f"📄 Récupération de : {url}")
            
            # Faire la requête HTTP (comme cliquer sur un lien)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()  # Lève exception si erreur HTTP
            
            # Parser le HTML (comme comprendre la structure de la page)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Politesse : attendre entre les requêtes
            time.sleep(self.delay)
            
            return soup
            
        except requests.RequestException as e:
            self.logger.error(f"❌ Erreur récupération {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Erreur parsing {url}: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """
        Nettoie le texte extrait
        
        Analogie : Comme corriger et reformater un texte 
        en supprimant les fautes et espaces en trop
        
        Args:
            text: Texte brut à nettoyer
            
        Returns:
            Texte nettoyé et formaté
        """
        if not text:
            return ""
        
        # Supprimer les espaces multiples
        text = ' '.join(text.split())
        
        # Supprimer les caractères de contrôle
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # Nettoyer les sauts de ligne multiples
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
        
        return text.strip()
    
    def extract_links(self, soup: BeautifulSoup, base_url: str = None) -> List[str]:
        """
        Extrait tous les liens d'une page
        
        Analogie : Comme faire une liste de tous les liens 
        cliquables sur une page web
        
        Args:
            soup: Page parsée
            base_url: URL de base pour les liens relatifs
            
        Returns:
            Liste des URLs complètes
        """
        if base_url is None:
            base_url = self.base_url
            
        links = []
        
        # Trouver tous les liens <a href="...">
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            
            # Convertir les liens relatifs en liens absolus
            # Ex: "/entreprises" → "https://service-public.fr/entreprises"
            full_url = urljoin(base_url, href)
            
            # Garder seulement les liens du même domaine
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                links.append(full_url)
        
        # Supprimer les doublons
        return list(set(links))
    
    def extract_text_content(self, soup: BeautifulSoup) -> str:
        """
        Extrait le contenu textuel principal d'une page
        
        Analogie : Comme copier seulement le texte principal 
        d'un article, sans les menus et publicités
        
        Args:
            soup: Page parsée
            
        Returns:
            Texte principal nettoyé
        """
        # Supprimer les éléments non-informatifs
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Extraire le texte
        text = soup.get_text()
        
        # Nettoyer et retourner
        return self.clean_text(text)
    
    def classify_domain(self, title: str, content: str, url: str) -> str:
        """
        Classe automatiquement le domaine d'un document
        
        Analogie : Comme trier automatiquement des documents 
        dans des classeurs selon leur contenu
        
        Args:
            title: Titre du document
            content: Contenu du document  
            url: URL source
            
        Returns:
            Domaine : 'juridique', 'rh', 'economique', ou 'autre'
        """
        # Mots-clés par domaine
        keywords = {
            'juridique': ['droit', 'loi', 'code', 'juridique', 'tribunal', 'justice', 'contrat', 'responsabilité'],
            'rh': ['salarié', 'emploi', 'recrutement', 'formation', 'rh', 'ressources humaines', 'travail'],
            'economique': ['économie', 'finance', 'aide', 'subvention', 'crédit', 'impôt', 'fiscal']
        }
        
        # Texte à analyser (titre + début du contenu)
        text_to_analyze = (title + " " + content[:500]).lower()
        
        # Compter les mots-clés par domaine
        domain_scores = {}
        for domain, words in keywords.items():
            score = sum(1 for word in words if word in text_to_analyze)
            domain_scores[domain] = score
        
        # Retourner le domaine avec le plus de mots-clés
        if max(domain_scores.values()) > 0:
            return max(domain_scores, key=domain_scores.get)
        else:
            return 'autre'
    
    def extract_document(self, url: str) -> Optional[ExtractedDocument]:
        """
        Extrait un document complet depuis une URL
        
        Méthode principale qui combine toutes les autres
        
        Args:
            url: URL du document à extraire
            
        Returns:
            ExtractedDocument ou None si échec
        """
        # Récupérer la page
        soup = self.get_page(url)
        if not soup:
            return None
        
        # Extraire titre
        title_tag = soup.find('title') or soup.find('h1')
        title = title_tag.get_text() if title_tag else "Sans titre"
        title = self.clean_text(title)
        
        # Extraire contenu
        content = self.extract_text_content(soup)
        if len(content) < 100:  # Ignorer les pages trop courtes
            self.logger.warning(f"⚠️ Contenu trop court pour {url}")
            return None
        
        # Classifier le domaine
        domain = self.classify_domain(title, content, url)
        
        # Créer le document
        document = ExtractedDocument(
            title=title,
            content=content,
            source_url=url,
            domain=domain,
            metadata={
                'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'content_length': len(content),
                'title_length': len(title)
            }
        )
        
        self.logger.info(f"✅ Document extrait : {title[:50]}... ({domain})")
        return document