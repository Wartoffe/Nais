package nais.ColumnarDBService.config;

import org.springframework.beans.factory.annotation.Configurable;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.cassandra.config.AbstractCassandraConfiguration;
import org.springframework.data.cassandra.config.SchemaAction;
import org.springframework.data.cassandra.core.cql.keyspace.CreateKeyspaceSpecification;
import org.springframework.data.cassandra.core.cql.keyspace.KeyspaceOption;
import org.springframework.data.cassandra.repository.config.EnableCassandraRepositories;

import java.util.Collections;
import java.util.List;

@Configuration
@EnableCassandraRepositories
public class CassandraConfig extends AbstractCassandraConfiguration {

    //isto sto i baza podataka u relacijama
    @Value("${spring.data.cassandra.keyspace-name}")
    private String KEYSPACE;

    @Value("${spring.data.cassandra.contact-points}")
    private String CONTACT_POINT;

    @Value("${spring.data.cassandra.port}")
    private int PORT;

    //automatski se kreira ako ne postoji kad se pokrene aplikacija
    @Value("${spring.data.cassandra.schema-action}")
    private String SCHEMA_ACTION;
    @Override
    public String getContactPoints() {
        return CONTACT_POINT;
    }

    @Override
    protected int getPort() {
        return PORT;
    }

    @Override
    public SchemaAction getSchemaAction() {
        return SchemaAction.valueOf(SCHEMA_ACTION);
    }

    @Override
    protected String getKeyspaceName() {
        return KEYSPACE;
    }
    @Override
    protected List<CreateKeyspaceSpecification> getKeyspaceCreations() {
        return Collections.singletonList(
                CreateKeyspaceSpecification.createKeyspace(KEYSPACE)
                        .ifNotExists()
                        .with(KeyspaceOption.DURABLE_WRITES, true)
                        .withSimpleReplication(3L)
        );
    }
    //3L je replikacijoni faktor koji kaze da se podaci cuvaju na 3 razlicita servera, gde ako jedan padne postoje druga dva

    @Override
    public String[] getEntityBasePackages() {
        return new String[]{"nais.ColumnarDBService.entity"};
    }
}
