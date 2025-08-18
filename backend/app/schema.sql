CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS questions (
  id BIGSERIAL PRIMARY KEY,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  keywords TEXT NOT NULL,
  category TEXT NOT NULL,
  embedding VECTOR(1024) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_questions_embedding
ON questions USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
