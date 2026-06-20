package nais.ColumnarDBService.config;

import nais.ColumnarDBService.saga.dto.BookVisibilitySagaEvent;
import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.support.converter.DefaultClassMapper;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.Map;

/**
 * Declares the choreography saga's RabbitMQ topology for ColumnarDBService.
 *
 * This service is the producer of *_REQUESTED events (createLoan /
 * returnBook) and the consumer of *_COMPLETED / *_FAILED events, which it
 * binds into its own results queue on the shared topic exchange.
 *
 * The message converter uses a logical type id ("BookVisibilitySagaEvent")
 * instead of the fully-qualified class name, so that this service's own
 * local copy of the DTO can be (de)serialized even though the search
 * service has its own separate copy of the same class in a different
 * package.
 */
@Configuration
public class RabbitMQConfig {

    @Value("${saga.rabbitmq.exchange}")
    private String sagaExchangeName;

    @Value("${saga.rabbitmq.queue.results}")
    private String resultsQueueName;

    @Value("${saga.rabbitmq.routing-key.hide-completed}")
    private String hideCompletedRoutingKey;

    @Value("${saga.rabbitmq.routing-key.hide-failed}")
    private String hideFailedRoutingKey;

    @Value("${saga.rabbitmq.routing-key.unhide-completed}")
    private String unhideCompletedRoutingKey;

    @Value("${saga.rabbitmq.routing-key.unhide-failed}")
    private String unhideFailedRoutingKey;

    @Bean
    public TopicExchange sagaExchange() {
        return new TopicExchange(sagaExchangeName, true, false);
    }

    @Bean
    public Queue bookVisibilityResultsQueue() {
        return new Queue(resultsQueueName, true);
    }

    @Bean
    public Binding hideCompletedBinding(Queue bookVisibilityResultsQueue, TopicExchange sagaExchange) {
        return BindingBuilder.bind(bookVisibilityResultsQueue).to(sagaExchange).with(hideCompletedRoutingKey);
    }

    @Bean
    public Binding hideFailedBinding(Queue bookVisibilityResultsQueue, TopicExchange sagaExchange) {
        return BindingBuilder.bind(bookVisibilityResultsQueue).to(sagaExchange).with(hideFailedRoutingKey);
    }

    @Bean
    public Binding unhideCompletedBinding(Queue bookVisibilityResultsQueue, TopicExchange sagaExchange) {
        return BindingBuilder.bind(bookVisibilityResultsQueue).to(sagaExchange).with(unhideCompletedRoutingKey);
    }

    @Bean
    public Binding unhideFailedBinding(Queue bookVisibilityResultsQueue, TopicExchange sagaExchange) {
        return BindingBuilder.bind(bookVisibilityResultsQueue).to(sagaExchange).with(unhideFailedRoutingKey);
    }

    @Bean
    public DefaultClassMapper sagaClassMapper() {
        DefaultClassMapper classMapper = new DefaultClassMapper();
        classMapper.setIdClassMapping(Map.of("BookVisibilitySagaEvent", BookVisibilitySagaEvent.class));
        return classMapper;
    }

    @Bean
    public MessageConverter sagaMessageConverter(DefaultClassMapper sagaClassMapper) {
        Jackson2JsonMessageConverter converter = new Jackson2JsonMessageConverter();
        converter.setClassMapper(sagaClassMapper);
        return converter;
    }

    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory, MessageConverter sagaMessageConverter) {
        RabbitTemplate template = new RabbitTemplate(connectionFactory);
        template.setMessageConverter(sagaMessageConverter);
        return template;
    }
}
