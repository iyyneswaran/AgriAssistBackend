-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- Drop the old table and function if they exist to apply the new vector dimension
drop function if exists match_schemes;
drop table if exists schemes;

-- Create the schemes table to store chunks and metadata
create table if not exists schemes (
  id bigserial primary key,
  title text,
  description text,
  eligibility text,
  region text,
  crop_type text,
  -- gemini-embedding-001 produces 3072-dimensional vectors
  embedding vector(3072)
);

-- Create a function to search for schemes based on vector similarity
create or replace function match_schemes (
  query_embedding vector(3072),
  match_count int default null
) returns table (
  id bigint,
  title text,
  description text,
  eligibility text,
  region text,
  crop_type text,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    schemes.id,
    schemes.title,
    schemes.description,
    schemes.eligibility,
    schemes.region,
    schemes.crop_type,
    1 - (schemes.embedding <=> query_embedding) as similarity
  from schemes
  order by schemes.embedding <=> query_embedding
  limit match_count;
end;
$$;
