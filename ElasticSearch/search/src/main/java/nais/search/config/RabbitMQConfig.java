package nais.search.config;

import nais.search.saga.dto.BookVisibilitySagaEvent;
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
 * Declares the choreography saga's RabbitMQ topology for the search
 * service.
 *
 * The search service is the consumer of *_REQUESTED events (it owns
 * the request queue) and the producer of *_COMPLETED / *_FAILED
 * events, which it publishes back onto the same shared topic exchange
 * for ColumnarDBService to consume.
 *
 * The message converter uses a logical type id ("BookVisibilitySagaEvent")
 * instead of the fully-qualified class name, so that this service's own
 * local copy of the DTO can be (de)serialized even though
 * ColumnarDBService has its own separate copy of the same class in a
 * different package.
 */
@Configuration
public class RabbitMQConfig {

    @Value("${saga.rabbitmq.exchange}")
    private String sagaExchangeName;

    @Value("${saga.rabbitmq.queue.requests}")
    private String requestsQueueName;

    @Value("${saga.rabbitmq.routing-key.hide-requested}")
    private String hideRequestedRoutingKey;

    @Value("${saga.rabbitmq.routing-key.unhide-requested}")
    private String unhideRequestedRoutingKey;

    @Bean
    public TopicExchange sagaExchange() {
        return new TopicExchange(sagaExchangeName, true, false);
    }

    @Bean
    public Queue bookVisibilityRequestsQueue() {
        return new Queue(requestsQueueName, true);
    }

    @Bean
    public Binding hideRequestedBinding(Queue bookVisibilityRequestsQueue, TopicExchange sagaExchange) {
        return BindingBuilder.bind(bookVisibilityRequestsQueue).to(sagaExchange).with(hideRequestedRoutingKey);
    }

    @Bean
    public Binding unhideRequestedBinding(Queue bookVisibilityRequestsQueue, TopicExchange sagaExchange) {
        return BindingBuilder.bind(bookVisibilityRequestsQueue).to(sagaExchange).with(unhideRequestedRoutingKey);
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
