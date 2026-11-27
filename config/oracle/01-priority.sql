-- Configure the reference priority-transaction demo in the Test Resources PDB.
WHENEVER SQLERROR EXIT SQL.SQLCODE
ALTER SESSION SET CONTAINER = FREEPDB1;

SET SERVEROUTPUT ON

-- Configure Oracle Priority Transactions for the appointment showcase when
-- this database image supports the feature. Missing parameters or configuration
-- failures are logged without blocking tablespace and user creation.
DECLARE
  v_supported_parameters NUMBER;
BEGIN
  SELECT COUNT(*)
  INTO v_supported_parameters
  FROM v$parameter
  WHERE name IN (
    'priority_txns_mode',
    'priority_txns_high_wait_target',
    'priority_txns_medium_wait_target'
  );

  IF v_supported_parameters = 3 THEN
    EXECUTE IMMEDIATE 'ALTER SYSTEM SET PRIORITY_TXNS_HIGH_WAIT_TARGET = 3 SCOPE=BOTH';
    EXECUTE IMMEDIATE 'ALTER SYSTEM SET PRIORITY_TXNS_MEDIUM_WAIT_TARGET = 3 SCOPE=BOTH';
    EXECUTE IMMEDIATE 'ALTER SYSTEM SET PRIORITY_TXNS_MODE = ''ROLLBACK'' SCOPE=BOTH';
    DBMS_OUTPUT.PUT_LINE('Oracle Priority Transactions enabled: mode=ROLLBACK, highWaitTarget=3s, mediumWaitTarget=3s');
  ELSE
    DBMS_OUTPUT.PUT_LINE('Oracle Priority Transactions are not available in this database image; the transaction-priority showcase will not demonstrate priority takeover.');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('WARNING: Oracle Priority Transactions could not be fully configured: ' || SQLERRM);
    DBMS_OUTPUT.PUT_LINE('Continuing petclinic setup; the transaction-priority showcase may not demonstrate priority takeover.');
END;
/


EXIT;
