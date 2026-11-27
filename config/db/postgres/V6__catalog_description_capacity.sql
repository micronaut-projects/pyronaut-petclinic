-- Match the request model's 500-character description constraint.
ALTER TABLE "CLINIC_SERVICE_OFFERINGS" ALTER COLUMN "DESCRIPTION" TYPE VARCHAR(500);
