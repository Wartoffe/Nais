package nais.ColumnarDBService.saga;

import nais.ColumnarDBService.saga.dto.BookVisibilitySagaEvent;
import nais.ColumnarDBService.saga.dto.SagaEventType;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * Publishes hide/unhide requests onto the shared saga exchange so the
 * search service can keep Elasticsearch's visible/hidden book state in
 * sync with Cassandra's available-copies count.
 * <p>
 * Both events are only ever published *after* the local Cassandra writes
 * for the originating createLoan/returnBook call have already succeeded
 * -- a saga step should never announce a state that hasn't actually been
 * committed locally yet.
 */
@Component
public class SagaEventPublisher {

    private final RabbitTemplate rabbitTemplate;
    private final String exchange;
    private final String hideRequestedRoutingKey;
    private final String unhideRequestedRoutingKey;

    public SagaEventPublisher(RabbitTemplate rabbitTemplate,
                               @Value("${saga.rabbitmq.exchange}") String exchange,
                               @Value("${saga.rabbitmq.routing-key.hide-requested}") String hideRequestedRoutingKey,
                               @Value("${saga.rabbitmq.routing-key.unhide-requested}") String unhideRequestedRoutingKey) {
        this.rabbitTemplate = rabbitTemplate;
        this.exchange = exchange;
        this.hideRequestedRoutingKey = hideRequestedRoutingKey;
        this.unhideRequestedRoutingKey = unhideRequestedRoutingKey;
    }

    /**
     * Published by createLoan once availableCopies has just dropped to 0.
     */
    public UUID publishHideRequested(String isbn, UUID bookId, String bookTitle, String bookGenre,
                                      UUID loanId, UUID memberId, LocalDateTime loanDate) {
        UUID sagaId = UUID.randomUUID();
        BookVisibilitySagaEvent event = new BookVisibilitySagaEvent();
        event.setSagaId(sagaId);
        event.setEventType(SagaEventType.HIDE_REQUESTED);
        event.setIsbn(isbn);
        event.setBookId(bookId);
        event.setBookTitle(bookTitle);
        event.setBookGenre(bookGenre);
        event.setLoanId(loanId);
        event.setMemberId(memberId);
        event.setLoanDate(loanDate);

        rabbitTemplate.convertAndSend(exchange, hideRequestedRoutingKey, event);
        return sagaId;
    }

    /**
     * Published by returnBook once availableCopies has just risen from 0.
     */
    public UUID publishUnhideRequested(String isbn, UUID bookId, String bookTitle, String bookGenre,
                                        UUID loanId, UUID memberId, LocalDateTime loanDate,
                                        String returnDate, LocalDateTime returnTimestamp) {
        UUID sagaId = UUID.randomUUID();
        BookVisibilitySagaEvent event = new BookVisibilitySagaEvent();
        event.setSagaId(sagaId);
        event.setEventType(SagaEventType.UNHIDE_REQUESTED);
        event.setIsbn(isbn);
        event.setBookId(bookId);
        event.setBookTitle(bookTitle);
        event.setBookGenre(bookGenre);
        event.setLoanId(loanId);
        event.setMemberId(memberId);
        event.setLoanDate(loanDate);
        event.setReturnDate(returnDate);
        event.setReturnTimestamp(returnTimestamp);

        rabbitTemplate.convertAndSend(exchange, unhideRequestedRoutingKey, event);
        return sagaId;
    }
}
