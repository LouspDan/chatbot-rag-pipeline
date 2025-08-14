#!/bin/bash
# Script de restructuration des tests

echo "🔄 Restructuration tests vers structure professionnelle..."

# Créer la structure
mkdir -p tests/{unit,integration}
mkdir -p scripts

# Déplacer tests unitaires (une classe = un test)
mv test_text_processor.py tests/unit/ 2>/dev/null || echo "test_text_processor.py déjà déplacé"
mv test_embeddings.py tests/unit/ 2>/dev/null || echo "test_embeddings.py déjà déplacé"

# Déplacer tests d'intégration (plusieurs modules)
mv test_pgvector.py tests/integration/ 2>/dev/null || echo "test_pgvector.py déjà déplacé"
mv test_service_public.py tests/integration/ 2>/dev/null || echo "test_service_public.py déjà déplacé"
mv test_complete_pipeline.py tests/integration/ 2>/dev/null || echo "test_complete_pipeline.py déjà déplacé"

# Créer scripts démo pour clients
cp tests/integration/test_complete_pipeline.py scripts/demo_complete_pipeline.py 2>/dev/null || echo "Démo déjà créée"

# Créer configuration pytest
cat > tests/conftest.py << 'EOF'
"""
Configuration pytest pour tests chatbot RAG pipeline
"""

import pytest
import sys
import os

# Ajouter le dossier racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def db_config():
    """Configuration base de données pour tests"""
    return {
        'host': 'localhost',
        'port': 5432,
        'database': 'chatbot_db',
        'user': 'chatbot_user',
        'password': 'chatbot_password'
    }

@pytest.fixture(scope="session") 
def test_document():
    """Document de test pour les tests"""
    from src.data_extraction.extractors.service_public import ServicePublicExtractor
    
    extractor = ServicePublicExtractor()
    doc = extractor.extract_single_test_fiche()
    
    if not doc:
        pytest.skip("Impossible de récupérer document de test")
    
    return doc
EOF

# Créer README pour tests
cat > tests/README.md << 'EOF'
# Tests Pipeline RAG

## Structure

- `unit/` : Tests unitaires (une classe/fonction)
- `integration/` : Tests d'intégration (plusieurs modules)

## Lancement

```bash
# Tous les tests
pytest tests/

# Tests unitaires seulement
pytest tests/unit/

# Tests d'intégration seulement  
pytest tests/integration/

# Test spécifique
pytest tests/unit/test_text_processor.py -v
```

## Prérequis

- PostgreSQL + pgvector en cours d'exécution
- Docker Compose lancé : `docker-compose up -d`
EOF

echo "✅ Restructuration terminée !"
echo "📁 Structure professionnelle créée"
echo "🧪 Tests organisés par type"
echo "📋 Scripts démo disponibles"