CREATE TABLE content_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    raw_content_id UUID NOT NULL REFERENCES raw_contents(id) ON DELETE CASCADE,
    UNIQUE(content_id, raw_content_id)
);
