package rs.ac.uns.acs.nais.TimeseriesDatabaseService.configuration;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.core.*;
import org.springframework.amqp.rabbit.config.SimpleRabbitListenerContainerFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.support.converter.DefaultJackson2JavaTypeMapper;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event.BookReturnedToSupplierEvent;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event.BudzetUpdateFailedEvent;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event.BudzetUpdatedEvent;

import java.util.Map;


@Configuration
public class RabbitMQConfig {
    // -------------------------------------------------------------------------
    // Exchange, queue, and routing-key name constants
    // -------------------------------------------------------------------------

    // -- CHOREOGRAPHY --
    public static final String CHOREOGRAPHY_EXCHANGE       = "saga.choreography.exchange";

    public static final String ORDERSTATUS_CREATED_QUEUE      = "orderstatus.created.queue";
    public static final String ORDERSTATUS_CREATED_KEY        = "orderstatus.created";

    public static final String BOOK_CREATED_QUEUE       = "book.created.queue";
    public static final String BOOK_CREATED_KEY         = "book.created";

    public static final String BOOK_CREATE_FAILED_QUEUE = "book.create.failed.queue";
    public static final String BOOK_CREATE_FAILED_KEY   = "book.create.failed";

    public static final String ORDERSTATUS_COMPENSATED_QUEUE  = "orderstatus.compensated.queue";
    public static final String ORDERSTATUS_COMPENSATED_KEY    = "orderstatus.compensated";


    // =========================================================================
    //  MARIJA konstante: vraćanje knjige dobavljaču
    // =========================================================================
    public static final String BOOK_RETURNED_TO_SUPPLIER_QUEUE = "book.returned.supplier.queue";
    public static final String BOOK_RETURNED_TO_SUPPLIER_KEY   = "book.returned.supplier";

    public static final String BUDGET_UPDATED_QUEUE = "budget.updated.queue";
    public static final String BUDGET_UPDATED_KEY   = "budget.updated";

    public static final String BUDGET_UPDATE_FAILED_QUEUE = "budget.update.failed.queue";
    public static final String BUDGET_UPDATE_FAILED_KEY   = "budget.update.failed";


    // =========================================================================
    // Message converter and RabbitTemplate
    // =========================================================================

    /** Converts Java objects to JSON messages and back for both sending and receiving. */
    @Bean
    public MessageConverter jsonMessageConverter() {

        ObjectMapper objectMapper = new ObjectMapper();
        objectMapper.registerModule(new JavaTimeModule());
        objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

        Jackson2JsonMessageConverter converter = new Jackson2JsonMessageConverter(objectMapper);

        DefaultJackson2JavaTypeMapper typeMapper = new DefaultJackson2JavaTypeMapper();
        typeMapper.setTrustedPackages("*");
        typeMapper.setIdClassMapping(Map.of(
                "bookReturnedToSupplierEvent", BookReturnedToSupplierEvent.class,
                "budgetUpdateFailedEvent", BudzetUpdateFailedEvent.class,
                "budgetUpdatedEvent", BudzetUpdatedEvent.class
        ));
        converter.setJavaTypeMapper(typeMapper);

        return converter;
    }

    /**
     * Configures RabbitTemplate with the JSON converter so all outbound messages
     * are serialized to JSON automatically.
     */
    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory) {
        RabbitTemplate template = new RabbitTemplate(connectionFactory);
        template.setMessageConverter(jsonMessageConverter());
        return template;
    }

    /**
     * Configures the @RabbitListener container factory with the JSON converter so
     * inbound messages are deserialized into the correct Java type automatically.
     */
    @Bean
    public SimpleRabbitListenerContainerFactory rabbitListenerContainerFactory(
            ConnectionFactory connectionFactory) {
        SimpleRabbitListenerContainerFactory factory = new SimpleRabbitListenerContainerFactory();
        factory.setConnectionFactory(connectionFactory);
        factory.setMessageConverter(jsonMessageConverter());
        return factory;
    }

    // =========================================================================
    // CHOREOGRAPHY -- exchange and bindings
    // =========================================================================

    /** TopicExchange for choreography -- supports wildcard routing keys. */
    @Bean
    public TopicExchange choreographyExchange() {
        return new TopicExchange(CHOREOGRAPHY_EXCHANGE);
    }

    @Bean public Queue orderstatusCreatedQueue()     { return QueueBuilder.durable(ORDERSTATUS_CREATED_QUEUE).build(); }
    @Bean public Queue bookCreatedQueue()      { return QueueBuilder.durable(BOOK_CREATED_QUEUE).build(); }
    @Bean public Queue bookCreateFailedQueue() { return QueueBuilder.durable(BOOK_CREATE_FAILED_QUEUE).build(); }
    @Bean public Queue orderstatusCompensatedQueue() { return QueueBuilder.durable(ORDERSTATUS_COMPENSATED_QUEUE).build(); }

    @Bean public Binding orderstatusCreatedBinding()     { return BindingBuilder.bind(orderstatusCreatedQueue()).to(choreographyExchange()).with(ORDERSTATUS_CREATED_KEY); }
    @Bean public Binding bookCreatedBinding()      { return BindingBuilder.bind(bookCreatedQueue()).to(choreographyExchange()).with(BOOK_CREATED_KEY); }
    @Bean public Binding bookCreateFailedBinding() { return BindingBuilder.bind(bookCreateFailedQueue()).to(choreographyExchange()).with(BOOK_CREATE_FAILED_KEY); }
    @Bean public Binding orderstatusCompensatedBinding() { return BindingBuilder.bind(orderstatusCompensatedQueue()).to(choreographyExchange()).with(ORDERSTATUS_COMPENSATED_KEY); }


    // =========================================================================
    //  MARIJA queue/binding beans: vraćanje knjige dobavljaču
    // =========================================================================

    @Bean public Queue bookReturnedToSupplierQueue() { return QueueBuilder.durable(BOOK_RETURNED_TO_SUPPLIER_QUEUE).build(); }
    @Bean public Queue budgetUpdatedQueue()             { return QueueBuilder.durable(BUDGET_UPDATED_QUEUE).build(); }
    @Bean public Queue budgetUpdateFailedQueue()         { return QueueBuilder.durable(BUDGET_UPDATE_FAILED_QUEUE).build(); }

    @Bean public Binding bookReturnedToSupplierBinding() { return BindingBuilder.bind(bookReturnedToSupplierQueue()).to(choreographyExchange()).with(BOOK_RETURNED_TO_SUPPLIER_KEY); }
    @Bean public Binding budgetUpdatedBinding()          { return BindingBuilder.bind(budgetUpdatedQueue()).to(choreographyExchange()).with(BUDGET_UPDATED_KEY); }
    @Bean public Binding budgetUpdateFailedBinding()     { return BindingBuilder.bind(budgetUpdateFailedQueue()).to(choreographyExchange()).with(BUDGET_UPDATE_FAILED_KEY); }

}
