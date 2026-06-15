-- HelpUSAI persistent memory migration v1
-- Target: Railway Postgres
-- Safety:
-- - Additive only.
-- - Uses create table if not exists.
-- - Uses create index if not exists.
-- - Does not delete or mutate existing data.
-- - Must be reviewed before production apply.

begin;

create table if not exists helpus_memory_events (
    id bigserial primary key,
    created_at timestamptz not null default now(),
    event_type text not null,
    source text not null,
    conversation_id text,
    actor text,
    summary text not null,
    details jsonb,
    safety_level text not null default 'normal',
    status text not null default 'recorded'
);

create index if not exists idx_helpus_memory_events_created_at
on helpus_memory_events (created_at);

create index if not exists idx_helpus_memory_events_conversation
on helpus_memory_events (conversation_id);

create index if not exists idx_helpus_memory_events_type
on helpus_memory_events (event_type);

create table if not exists helpus_memory_feedback (
    id bigserial primary key,
    created_at timestamptz not null default now(),
    event_id bigint,
    feedback_type text not null,
    source text not null,
    summary text not null,
    severity text not null default 'info',
    status text not null default 'draft',
    details jsonb
);

create index if not exists idx_helpus_memory_feedback_status
on helpus_memory_feedback (status);

create index if not exists idx_helpus_memory_feedback_event_id
on helpus_memory_feedback (event_id);

create table if not exists helpus_memory_lessons (
    id bigserial primary key,
    created_at timestamptz not null default now(),
    source_feedback_id bigint,
    title text not null,
    lesson text not null,
    status text not null default 'draft',
    confidence double precision not null default 0.0,
    details jsonb
);

create index if not exists idx_helpus_memory_lessons_status
on helpus_memory_lessons (status);

create index if not exists idx_helpus_memory_lessons_source_feedback_id
on helpus_memory_lessons (source_feedback_id);

create table if not exists helpus_memory_rules (
    id bigserial primary key,
    created_at timestamptz not null default now(),
    source_lesson_id bigint,
    rule_key text not null,
    rule_text text not null,
    status text not null default 'draft',
    details jsonb
);

create unique index if not exists ux_helpus_memory_rules_key_status
on helpus_memory_rules (rule_key, status);

create index if not exists idx_helpus_memory_rules_source_lesson_id
on helpus_memory_rules (source_lesson_id);

commit;
