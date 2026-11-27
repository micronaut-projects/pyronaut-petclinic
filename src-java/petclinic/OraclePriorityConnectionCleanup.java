package petclinic;

import com.zaxxer.hikari.HikariDataSource;
import io.micronaut.data.connection.ConnectionStatus;
import io.micronaut.data.connection.ConnectionSynchronization;
import io.micronaut.data.connection.jdbc.advice.DelegatingDataSource;
import io.micronaut.transaction.TransactionDefinition;
import io.micronaut.transaction.annotation.OracleTransactional;
import io.micronaut.transaction.support.TransactionExecutionListener;
import jakarta.inject.Named;
import jakarta.inject.Singleton;

import javax.sql.DataSource;
import java.sql.Connection;

/** Retire LOW demo sessions after transaction cleanup; see PORT-054. */
@Singleton
public final class OraclePriorityConnectionCleanup implements TransactionExecutionListener<Connection> {
    private final DataSource dataSource;

    public OraclePriorityConnectionCleanup(@Named("default") DataSource dataSource) {
        this.dataSource = DelegatingDataSource.unwrapDataSource(dataSource);
    }

    @Override
    public void afterBegin(ConnectionStatus<Connection> status, TransactionDefinition definition) {
        Object priority = definition.getProperties().get(OracleTransactional.ORACLE_PRIORITY);
        if (!(dataSource instanceof HikariDataSource pool)
                || !(OracleTransactional.Priority.LOW.equals(priority) || "LOW".equals(priority))) {
            return;
        }
        // On the verified Oracle/JDBC versions, reusing a session after a priority
        // rollback can silently allow a later LOW request to overwrite HIGH.
        // Keep the real transaction/error handling, then discard only its session.
        status.registerSynchronization(new ConnectionSynchronization() {
            @Override
            public int getOrder() {
                return LOWEST_PRECEDENCE;
            }

            @Override
            public void beforeClosed() {
                pool.evictConnection(status.getConnection());
            }
        });
    }
}
