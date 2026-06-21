package nais.search.saga;

import nais.search.saga.dto.BookVisibilitySagaEvent;
import nais.search.service.BookService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

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
