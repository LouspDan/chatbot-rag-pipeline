-- Création de l'extension pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Table pour stocker les documents sources
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    source_url TEXT,
    content TEXT NOT NULL,
    domain VARCHAR(100), -- 'juridique', 'rh', 'economique'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table pour stocker les chunks de texte avec embeddings
CREATE TABLE IF NOT EXISTS text_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(384), -- Dimension pour all-MiniLM-L6-v2
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche vectorielle rapide
CREATE INDEX IF NOT EXISTS text_chunks_embedding_idx 
ON text_chunks USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Index pour filtrage par domaine
CREATE INDEX IF NOT EXISTS documents_domain_idx ON documents(domain);
CREATE INDEX IF NOT EXISTS documents_created_at_idx ON documents(created_at);

-- Table pour le monitoring du pipeline
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    run_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(50) NOT NULL, -- 'running', 'success', 'failed'
    documents_processed INTEGER DEFAULT 0,
    chunks_generated INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    execution_time_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger pour documents
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insertion de données de test
INSERT INTO documents (title, source_url, content, domain) VALUES 
('Test Document', 'https://example.com', 'Ceci est un document de test pour valider la configuration.', 'test')
ON CONFLICT DO NOTHING;