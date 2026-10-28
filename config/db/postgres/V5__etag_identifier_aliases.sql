-- Micronaut Data's generated ETag read transformer does not quote mapped
-- identifiers. PostgreSQL folds those references to lowercase. These computed
-- aliases expose the same values and cannot be changed independently.
ALTER TABLE "VETS" ADD first_name VARCHAR(255) GENERATED ALWAYS AS ("FIRST_NAME") STORED;
ALTER TABLE "VETS" ADD last_name VARCHAR(255) GENERATED ALWAYS AS ("LAST_NAME") STORED;
ALTER TABLE "VETS" ADD specialities_etag_hash VARCHAR(64) GENERATED ALWAYS AS ("SPECIALITIES_ETAG_HASH") STORED;
