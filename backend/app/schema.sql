-- Embedding için extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Soru tablosu
CREATE TABLE IF NOT EXISTS questions (
  id BIGSERIAL PRIMARY KEY,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  keywords TEXT NOT NULL,
  category TEXT NOT NULL,
  embedding VECTOR(1024) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Embedding araması için ivfflat index
CREATE INDEX IF NOT EXISTS idx_questions_embedding
ON questions USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- [Yeni] Listelemeler için created_at index
CREATE INDEX IF NOT EXISTS idx_questions_created_at
ON questions (created_at DESC);

-- [Yeni] Aynı sorunun tekrar kaydedilmesini önlemek için unique index
CREATE UNIQUE INDEX IF NOT EXISTS uq_questions_text
ON questions ((lower(trim(question))));
