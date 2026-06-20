package rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography;

import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.configuration.RabbitMQConfig;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaStatusaPorudzbine;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.repository.LibraryInfluxRepositoryImpl;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event.BookCreationFailedEvent;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event.OrderStatusCompensatedEvent;

import java.time.Instant;
import java.time.LocalDateTime;
import java.util.List;

/*
 * Slusa BookCreationFailedEvent koji objavljuje VectorDatabaseService kada upis
 * knjige u Milvus (i kreiranje embedding-a) ne uspe.
 *
 * Kompenzacija: pošto je InfluxDB append-only (nema delete/update), "rollback" se
 * radi upisom NOVOG korektivnog zapisa koji vraca prethodno aktivni status
 * porudzbine. Nakon uspesne kompenzacije objavljuje se OrderStatusCompensatedEvent,
 * radi audit traga i da bi eventualni drugi zainteresovani servisi mogli da reaguju.
 */
@Slf4j
@Component
public class CompensationListener {

    private final LibraryInfluxRepositoryImpl repository;
    private final RabbitTemplate rabbitTemplate;

    public CompensationListener(LibraryInfluxRepositoryImpl repository, RabbitTemplate rabbitTemplate) {
        this.repository = repository;
        this.rabbitTemplate = rabbitTemplate;
    }

    @RabbitListener(queues = RabbitMQConfig.BOOK_CREATE_FAILED_QUEUE)
    public void handleBookCreationFailed(BookCreationFailedEvent event) {
        log.warn("[CHOREOGRAPHY] sagaId={} -- primljen BookCreationFailedEvent za narudzbinaid={}, razlog={}",
                event.getSagaId(), event.getNarudzbinaid(), event.getRazlog());

        List<PromenaStatusaPorudzbine> pretposlednji =
                repository.findSecondToLastStatusByNarudzbinaid(event.getNarudzbinaid());

        if (pretposlednji.isEmpty()) {
            log.error("[CHOREOGRAPHY] sagaId={} -- nema pretposlednjeg statusa, kompenzacija nije moguca za narudzbinaid={}",
                    event.getSagaId(), event.getNarudzbinaid());
            return;
        }

        PromenaStatusaPorudzbine prethodniStatus = pretposlednji.getFirst();
        prethodniStatus.setTimestamp(Instant.now());

        try {
            repository.saveStatusPromena(prethodniStatus);
            log.info("[CHOREOGRAPHY] sagaId={} -- kompenzacija uspesna, narudzbinaid={} vracen na noviStatus={}",
                    event.getSagaId(), event.getNarudzbinaid(), prethodniStatus.getNoviStatus());

            OrderStatusCompensatedEvent compensated = new OrderStatusCompensatedEvent(
                    event.getSagaId(),
                    event.getNarudzbinaid(),
                    prethodniStatus.getNoviStatus(),
                    LocalDateTime.now());

            rabbitTemplate.convertAndSend(
                    RabbitMQConfig.CHOREOGRAPHY_EXCHANGE,
                    RabbitMQConfig.ORDERSTATUS_COMPENSATED_KEY,
                    compensated);
            log.info("[CHOREOGRAPHY] sagaId={} -- OrderStatusCompensatedEvent objavljen", event.getSagaId());
        } catch (Exception e) {
            log.error("[CHOREOGRAPHY] sagaId={} -- GRESKA prilikom kompenzacije za narudzbinaid={}: {}",
                    event.getSagaId(), event.getNarudzbinaid(), e.getMessage(), e);
        }
    }
}