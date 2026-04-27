-- 1. categories
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. raw_contents
CREATE TABLE raw_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    source TEXT NOT NULL,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    tags TEXT[] NOT NULL DEFAULT '{}',
    embedding_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. notion_sources
CREATE TABLE notion_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_content_id UUID NOT NULL REFERENCES raw_contents(id) ON DELETE CASCADE,
    notion_page_id TEXT NOT NULL UNIQUE,
    notion_url TEXT NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4. contents
CREATE TABLE contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    tags TEXT[] NOT NULL DEFAULT '{}',
    embedding_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5. publications
CREATE TABLE publications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'converted',
    published_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);