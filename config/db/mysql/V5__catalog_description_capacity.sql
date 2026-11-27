-- Match the request model's 500-character description constraint.
ALTER TABLE CLINIC_SERVICE_OFFERINGS MODIFY DESCRIPTION VARCHAR(500) NULL;
