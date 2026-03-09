-- 在 Supabase SQL 编辑器中执行，用于保存占卜历史
create table if not exists readings (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  spread_type text not null,
  question text,
  cards jsonb not null,
  interpretation text not null,
  created_at timestamptz default now()
);

create index if not exists readings_user_id_idx on readings (user_id);
