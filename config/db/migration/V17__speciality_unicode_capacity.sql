-- The speciality request model also permits 255 characters, not bytes.
ALTER TABLE SPECIALTIES MODIFY NAME VARCHAR2(255 CHAR);
