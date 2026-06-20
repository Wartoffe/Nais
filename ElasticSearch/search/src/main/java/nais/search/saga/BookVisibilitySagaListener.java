package nais.search.saga;

import nais.search.saga.dto.BookVisibilitySagaEvent;
import nais.search.service.BookService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

/**
 * Choreography saga participant on the search service side.
 * <p>
 * Consumes HIDE_REQUESTED / UNHIDE_REQUESTED events published by
 * ColumnarDBService, performs the corresponding logical delete/undelete
 * locally, and reports the outcome back on the saga exchange.
 * <p>
 * Any exception is caught here on purpose: a thrown exception would let
 * RabbitMQ requeue/redeliver the message indefinitely (since no manual
 * ack/dead-lettering is configured), which would never let the saga reach
 * a terminal state. Instead, every failure is translated into an explicit
 * *_FAILED event, which is what actually drives compensation on the
 * ColumnarDBService side.
 */
@Component
public class BookVisibilitySagaListener {

    private static final Logger log = LoggerFactory.getLogger(BookVisibilitySagaListener.class);

    private final BookService bookService;
    private final SagaEventPublisher publisher;

    public BookVisibilitySagaListener(BookService bookService, SagaEventPublisher publisher) {
        this.bookService = bookService;
        this.publisher = publisher;
    }

    @RabbitListener(queues = "${saga.rabbitmq.queue.requests}")
    public void onHideRequested(BookVisibilitySagaEvent event) {
        switch (event.getEventType()) {
            case HIDE_REQUESTED -> handleHide(event);
            case UNHIDE_REQUESTED -> handleUnhide(event);
            default -> log.warn("Ignoring unexpected saga event type {} on requests queue", event.getEventType());
        }
    }

    private void handleHide(BookVisibilitySagaEvent event) {
        try {
            bookService.hideBooksByIsbn(event.getIsbn());
            log.info("Hid book(s) with isbn={} for saga {}", event.getIsbn(), event.getSagaId());
            publisher.publishHideCompleted(event);
        } catch (Exception ex) {
            log.warn("Failed to hide book(s) with isbn={} for saga {}: {}", event.getIsbn(), event.getSagaId(), ex.getMessage());
            publisher.publishHideFailed(event, ex.getMessage());
        }
    }

    private void handleUnhide(BookVisibilitySagaEvent event) {
        try {
            bookService.unhideBooksByIsbn(event.getIsbn());
            log.info("Unhid book(s) with isbn={} for saga {}", event.getIsbn(), event.getSagaId());
            publisher.publishUnhideCompleted(event);
        } catch (Exception ex) {
            log.warn("Failed to unhide book(s) with isbn={} for saga {}: {}", event.getIsbn(), event.getSagaId(), ex.getMessage());
            publisher.publishUnhideFailed(event, ex.getMessage());
        }
    }
}
