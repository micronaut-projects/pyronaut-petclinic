-- Native generated ETags use id, first name, last name and assignment hash.
ALTER TABLE "VETS" ADD "SPECIALITIES_ETAG_HASH" VARCHAR(64) DEFAULT 'E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855' NOT NULL;

UPDATE "VETS" v SET "SPECIALITIES_ETAG_HASH" = (
    SELECT UPPER(encode(sha256(convert_to(COALESCE(string_agg(vs."SPECIALTY_ID"::text, ',' ORDER BY vs."SPECIALTY_ID"), ''), 'UTF8')), 'hex'))
    FROM "VET_SPECIALTIES" vs WHERE vs."VET_ID" = v.id);

CREATE OR REPLACE FUNCTION SYS_ROW_ETAG(INTEGER, VARCHAR, VARCHAR, VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
IMMUTABLE
AS $$
SELECT upper(md5(
    CASE WHEN $1 IS NULL THEN '-1:' ELSE length($1::text)::text || ':' || $1::text END ||
    CASE WHEN $2 IS NULL THEN '-1:' ELSE length($2)::text || ':' || $2 END ||
    CASE WHEN $3 IS NULL THEN '-1:' ELSE length($3)::text || ':' || $3 END ||
    CASE WHEN $4 IS NULL THEN '-1:' ELSE length($4)::text || ':' || $4 END
))::varchar
$$;
