package nais.search.saga;

import nais.search.saga.dto.BookVisibilitySagaEvent;
import nais.search.saga.dto.SagaEventType;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class SagaEventPublisher {

    private final RabbitTemplate rabbitTemplate;
    private final String exchange;
    private final String hideCompletedRoutingKey;
    private final String hideFailedRoutingKey;
    private final String unhideCompletedRoutingKey;
    private final String unhideFailedRoutingKey;

    public SagaEventPublisher(RabbitTemplate rabbitTemplate,
                               @Value("${saga.rabbitmq.exchange}") String exchange,
                               @Value("${saga.rabbitmq.routing-key.hide-completed}") String hideCompletedRoutingKey,
                               @Value("${saga.rabbitmq.routing-key.hide-failed}") String hideFailedRoutingKey,
                               @Value("${saga.rabbitmq.routing-key.unhide-completed}") String unhideCompletedRoutingKey,
                               @Value("${saga.rabbitmq.routing-key.unhide-failed}") String unhideFailedRoutingKey) {
        this.rabbitTemplate = rabbitTemplate;
        this.exchange = exchange;
        this.hideCompletedRoutingKey = hideCompletedRoutingKey;
        this.hideFailedRoutingKey = hideFailedRoutingKey;
        this.unhideCompletedRoutingKey = unhideCompletedRoutingKey;
        this.unhideFailedRoutingKey = unhideFailedRoutingKey;
    }

    public void publishHideCompleted(BookVisibilitySagaEvent original) {
        BookVisibilitySagaEvent event = echo(original, SagaEventType.HIDE_COMPLETED, null);
        rabbitTemplate.convertAndSend(exchange, hideCompletedRoutingKey, event);
    }

    public void publishHideFailed(BookVisibilitySagaEvent original, String reason) {
        BookVisibilitySagaEvent event = echo(original, SagaEventType.HIDE_FAILED, reason);
        rabbitTemplate.convertAndSend(exchange, hideFailedRoutingKey, event);
    }

    public void publishUnhideCompleted(BookVisibilitySagaEvent original) {
        BookVisibilitySagaEvent event = echo(original, SagaEventType.UNHIDE_COMPLETED, null);
        rabbitTemplate.convertAndSend(exchange, unhideCompletedRoutingKey, event);
    }

    public void publishUnhideFailed(BookVisibilitySagaEvent original, String reason) {
        BookVisibilitySagaEvent event = echo(original, SagaEventType.UNHIDE_FAILED, reason);
        rabbitTemplate.convertAndSend(exchange, unhideFailedRoutingKey, event);
    }

    private BookVisibilitySagaEvent echo(BookVisibilitySagaEvent original, SagaEventType type, String reason) {
        BookVisibilitySagaEvent event = new BookVisibilitySagaEvent();
        event.setSagaId(original.getSagaId());
        event.setEventType(type);
        event.setIsbn(original.getIsbn());
        event.setBookId(original.getBookId());
        event.setBookTitle(original.getBookTitle());
        event.setBookGenre(original.getBookGenre());
        event.setLoanId(original.getLoanId());
        event.setMemberId(original.getMemberId());
        event.setLoanDate(original.getLoanDate());
        event.setReturnDate(original.getReturnDate());
        event.setReturnTimestamp(original.getReturnTimestamp());
        event.setReason(reason);
        return event;
    }
}
