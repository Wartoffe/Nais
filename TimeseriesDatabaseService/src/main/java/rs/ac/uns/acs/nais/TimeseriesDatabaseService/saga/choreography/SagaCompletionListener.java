package rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography;

import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.configuration.RabbitMQConfig;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event.BookCreatedEvent;

/*
 * Slusa BookCreatedEvent koji objavljuje VectorDatabaseService nakon sto USPESNO upise
 * sve knjige iz ChangeOfOrderStatusCreatedEvent-a u Milvus.
 *
 * Ovo je tacka u kojoj se, sa stanovista TimeseriesDatabaseService, koreografisana SAGA
 * zvanicno smatra USPESNO zavrsenom (svi koraci su prosli).
 * Nijedan drugi servis vise ne ucestvuje nakon ovog koraka, pa je ovo prirodno mesto da se
 * to zabelezi (audit log).
 */
@Slf4j
@Component
public class SagaCompletionListener {
    @RabbitListener(queues = RabbitMQConfig.BOOK_CREATED_QUEUE)
    public void handleBookCreated(BookCreatedEvent event) {
        log.info("[CHOREOGRAPHY] sagaId={} USPESNO ZAVRSENA -- primljen BookCreatedEvent za narudzbinaid={}, timestamp={} ", event.getSagaId(), event.getNarudzbinaid(), event.getTimestamp());
    }
}
