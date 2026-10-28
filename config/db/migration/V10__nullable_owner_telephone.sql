-- The reference owner-care document permits a null telephone value.
-- Ordinary owner forms continue to require and validate telephone numbers.
ALTER TABLE OWNERS MODIFY (TELEPHONE NULL);
