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
  created_at TIMESTAMP DEFAULT NOW(),
  created_by VARCHAR(100) DEFAULT 'anonymous',
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Embedding araması için ivfflat index
CREATE INDEX IF NOT EXISTS idx_questions_embedding
ON questions USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Listelemeler için created_at index
CREATE INDEX IF NOT EXISTS idx_questions_created_at
ON questions (created_at DESC);

-- updated_at için index (güncelleme geçmişini takip etmek için)
CREATE INDEX IF NOT EXISTS idx_questions_updated_at
ON questions (updated_at DESC);

-- Aynı sorunun tekrar kaydedilmesini önlemek için unique index
CREATE UNIQUE INDEX IF NOT EXISTS uq_questions_text
ON questions ((lower(trim(question))));

-- created_by kolonu için index (performans için)
CREATE INDEX IF NOT EXISTS idx_questions_created_by
ON questions (created_by);

-- Mevcut tabloya created_by kolonu ekleme (eğer yoksa)
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'questions' AND column_name = 'created_by') THEN
        ALTER TABLE questions ADD COLUMN created_by VARCHAR(100) DEFAULT 'anonymous';
    END IF;
END $$;

-- Mevcut tabloya updated_at kolonu ekleme (eğer yoksa)
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'questions' AND column_name = 'updated_at') THEN
        ALTER TABLE questions ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();
    END IF;
END $$;

-- updated_at otomatik güncelleme için trigger function
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- updated_at trigger'ı oluştur (eğer yoksa)
DROP TRIGGER IF EXISTS update_questions_modtime ON questions;
CREATE TRIGGER update_questions_modtime
    BEFORE UPDATE ON questions
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();