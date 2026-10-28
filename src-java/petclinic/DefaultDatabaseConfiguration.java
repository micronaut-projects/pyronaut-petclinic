package petclinic;

import io.micronaut.context.ApplicationContextBuilder;
import io.micronaut.context.ApplicationContextConfigurer;
import io.micronaut.context.annotation.ContextConfigurer;
import io.micronaut.context.env.MapPropertySource;
import io.micronaut.context.env.PropertySource;

import java.util.List;
import java.util.Map;
import java.util.Optional;

/** Supply H2 defaults only when no datasource dialect has been configured. */
@ContextConfigurer
public final class DefaultDatabaseConfiguration implements ApplicationContextConfigurer {
    private static final String DEFAULT_DIALECT_PROPERTY = "datasources.default.dialect";

    @Override
    public void configure(ApplicationContextBuilder builder) {
        // Inspect loaded sources before property processing and bean creation.
        // Custom profile names and programmatic overrides must also suppress H2.
        builder.propertySourcesLocator(environment -> {
            if (environment.getPropertySources().stream().anyMatch(DefaultDatabaseConfiguration::hasDialect)) {
                return List.of();
            }
            return environment.getPropertySourceLoaders().stream()
                    .filter(loader -> loader.getExtensions().contains("toml"))
                    .map(loader -> loader.load("application-h2", environment))
                    .flatMap(Optional::stream)
                    .toList();
        });
    }

    private static boolean hasDialect(PropertySource source) {
        // Inspect stored configuration only. Lazy sources can return a synthetic
        // value for any key, even when that key has not been configured.
        if (!(source instanceof MapPropertySource mapSource)) {
            return false;
        }
        Map<String, Object> properties = mapSource.asMap();
        if (properties.containsKey(DEFAULT_DIALECT_PROPERTY)
                || properties.containsKey("DATASOURCES_DEFAULT_DIALECT")) {
            return true;
        }
        // TOML/YAML property sources can retain their nested map representation.
        return properties.get("datasources") instanceof Map<?, ?> datasources
                && datasources.get("default") instanceof Map<?, ?> datasource
                && datasource.containsKey("dialect");
    }
}
