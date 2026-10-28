-- Preserve existing rows and foreign keys while matching the reference model.
ALTER TABLE PET_TYPES RENAME TO TYPES;
RENAME PET_TYPES_SEQ TO TYPES_SEQ;
