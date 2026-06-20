package rs.ac.uns.acs.nais.TimeseriesDatabaseService.configuration;

import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.core.*;
import org.springframework.amqp.rabbit.config.SimpleRabbitListenerContainerFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

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
    // Message converter and RabbitTemplate
    // =========================================================================

    /** Converts Java objects to JSON messages and back for both sending and receiving. */
    @Bean
    public MessageConverter jsonMessageConverter() {
        return new Jackson2JsonMessageConverter();
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
}
