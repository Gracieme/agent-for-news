-- agent_digests 表：存储每日推送，供网站「学习天地」读取
-- 可重复执行，不会报错

create table if not exists agent_digests (
  date text primary key,
  digest jsonb not null,
  created_at timestamptz default now()
);

alter table agent_digests enable row level security;

drop policy if exists "Allow public read" on agent_digests;
create policy "Allow public read" on agent_digests for select using (true);
