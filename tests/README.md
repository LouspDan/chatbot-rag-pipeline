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
