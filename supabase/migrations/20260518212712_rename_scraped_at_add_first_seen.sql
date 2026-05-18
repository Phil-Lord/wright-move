alter table "public"."listings" rename column "scraped_at" to "last_seen";

alter table "public"."listings"
    add column "first_seen" timestamp with time zone not null default now();

update "public"."listings" set "first_seen" = "last_seen";
