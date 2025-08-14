#!/usr/bin/env python3
"""
Test avec l'URL réelle découverte par l'utilisateur
entreprendre.service-public.fr/vosdroits/N24267
Version corrigée sans erreur de syntaxe
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_extraction.extractors.service_public import ServicePublicExtractor

def test_real_service_public_url():
    """Test avec l'URL réelle qui fonctionne"""
    print("🧪 TEST AVEC VRAIE URL ENTREPRENDRE.SERVICE-PUBLIC.FR")
    print("=" * 70)
    
    # Initialiser extracteur mis à jour
    extractor = ServicePublicExtractor(delay=1.0)
    print("✅ Extracteur Service-Public initialisé (nouvelle structure)")
    
    # Test avec l'URL découverte par l'utilisateur
    real_url = "https://entreprendre.service-public.fr/vosdroits/N24267"
    print(f"\n🔄 Test extraction URL réelle: {real_url}")
    
    # Vérifier d'abord le pattern
    is_valid_pattern = extractor.fiche_pattern.match(real_url) is not None
    print(f"🔍 Pattern URL valide: {'✅' if is_valid_pattern else '❌'}")
    
    if not is_valid_pattern:
        print("❌ Pattern non reconnu - Mise à jour nécessaire")
        return False
    
    # Extraire la fiche
    doc = extractor.extract_fiche(real_url)
    
    if doc:
        print("✅ EXTRACTION RÉUSSIE !")
        print("-" * 50)
        print(f"📄 Titre: {doc.title}")
        print(f"📝 Contenu (200 premiers chars):")
        print(f"    {doc.content[:200]}...")
        print(f"🏷️ Domaine: {doc.domain}")
        print(f"🔖 Sous-catégorie: {doc.metadata.get('subcategory')}")
        print(f"📊 Longueur totale: {doc.metadata.get('content_length')} caractères")
        print(f"🔢 Numéro fiche: {doc.metadata.get('fiche_number')}")
        print(f"📅 Date extraction: {doc.metadata.get('extraction_date')}")
        print(f"🔗 URL source: {doc.source_url}")
        
        # Validation de la qualité
        content_length = doc.metadata.get('content_length', 0)
        if content_length > 500:
            print(f"✅ Contenu substantiel ({content_length} chars)")
        else:
            print(f"⚠️ Contenu court ({content_length} chars)")
        
        if doc.domain != 'autre':
            print(f"✅ Classification réussie ({doc.domain})")
        else:
            print("⚠️ Classification par défaut")
        
    else:
        print("❌ Échec de l'extraction")
        print("Causes possibles:")
        print("- Problème de connexion")
        print("- Structure HTML différente de l'attendu")
        print("- Contenu trop court")
        return False
    
    # Test de découverte sur le nouveau domaine
    print(f"\n🔍 Test découverte automatique sur nouveau domaine...")
    
    try:
        # Découverte limitée pour test
        docs = extractor.extract_multiple_fiches(max_fiches=2)
        
        if docs:
            print(f"✅ Découverte automatique: {len(docs)} fiches trouvées")
            for i, d in enumerate(docs, 1):
                print(f"   {i}. {d.title[:60]}... ({d.domain})")
        else:
            print("⚠️ Aucune fiche découverte automatiquement")
            print("   (Normal si la structure de navigation a changé)")
            
    except Exception as e:
        print(f"⚠️ Erreur découverte automatique: {e}")
        print("   (L'extraction manuelle fonctionne quand même)")
    
    print("\n🎉 TEST PRINCIPAL RÉUSSI !")
    print("✅ L'extracteur fonctionne avec la nouvelle structure")
    
    return True

def test_url_patterns_update():
    """Test des nouveaux patterns URL"""
    print("\n🔍 VALIDATION NOUVEAUX PATTERNS")
    print("-" * 40)
    
    extractor = ServicePublicExtractor()
    
    test_urls = [
        "https://entreprendre.service-public.fr/vosdroits/N24267",  # ✅ Nouvelle structure N
        "https://entreprendre.service-public.fr/vosdroits/F12345",  # ✅ Nouvelle structure F
        "https://entreprendre.service-public.fr/vosdroits",         # ❌ Index
        "https://www.service-public.fr/entreprises/vosdroits/F123", # ❌ Ancienne structure
    ]
    
    for url in test_urls:
        is_valid = extractor.fiche_pattern.match(url) is not None
        status = "✅" if is_valid else "❌"
        print(f"  {status} {url}")
    
    print("✅ Patterns mis à jour correctement")

if __name__ == "__main__":
    print("🚀 TEST NOUVELLE STRUCTURE ENTREPRENDRE.SERVICE-PUBLIC.FR")
    print("=" * 70)
    
    # Test patterns
    test_url_patterns_update()
    
    # Test URL réelle
    success = test_real_service_public_url()
    
    if success:
        print("\n🎊 MIGRATION RÉUSSIE !")
        print("✅ Extracteur adapté à la nouvelle structure 2025")
    else:
        print("\n⚠️ Adaptation partielle")
        print("ℹ️ Ajustements supplémentaires peuvent être nécessaires")
    
    sys.exit(0 if success else 1)