package nais.ColumnarDBService.saga;

import nais.ColumnarDBService.saga.dto.BookVisibilitySagaEvent;
import nais.ColumnarDBService.service.LoanService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;



//ceka na *_COMPLETED / *_FAILED

@Component
public class BookVisibilitySagaListener {

    private static final Logger log = LoggerFactory.getLogger(BookVisibilitySagaListener.class);

    private final LoanService loanService;

    public BookVisibilitySagaListener(LoanService loanService) {
        this.loanService = loanService;
    }

    @RabbitListener(queues = "${saga.rabbitmq.queue.results}")
    public void onBookVisibilityResult(BookVisibilitySagaEvent event) {
        try {
            switch (event.getEventType()) {
                case HIDE_COMPLETED -> log.info("Saga {} hide completed for isbn={}", event.getSagaId(), event.getIsbn());
                case UNHIDE_COMPLETED -> log.info("Saga {} unhide completed for isbn={}", event.getSagaId(), event.getIsbn());
                case HIDE_FAILED -> {
                    log.warn("Saga {} hide FAILED for isbn={} (reason: {}), compensating createLoan for loan {}",
                            event.getSagaId(), event.getIsbn(), event.getReason(), event.getLoanId());
                    loanService.compensateCreateLoan(event.getMemberId(), event.getLoanDate(), event.getLoanId(),
                            event.getBookId(), event.getBookGenre(), event.getBookTitle());
                }
                case UNHIDE_FAILED -> {
                    log.warn("Saga {} unhide FAILED for isbn={} (reason: {}), compensating returnBook for loan {}",
                            event.getSagaId(), event.getIsbn(), event.getReason(), event.getLoanId());
                    loanService.compensateReturnBook(event.getMemberId(), event.getLoanId(), event.getBookId(),
                            event.getBookGenre(), event.getBookTitle(), event.getReturnDate(), event.getReturnTimestamp());
                }
                default -> log.warn("Ignoring unexpected saga event type {} on results queue", event.getEventType());
            }
        } catch (Exception ex) {
            log.error("Unhandled error while processing saga result {}: {}", event, ex.getMessage(), ex);
        }
    }
}
