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
        log.warn("[CHOREOGRAPHY] sagaId={} -- primljen BookCreationFailedEvent za narudzbinaid={}, razlog={}", event.getSagaId(), event.getNarudzbinaid(), event.getRazlog());

        String prethodniStatus = event.getPrethodniStatus();

        if (prethodniStatus == null || prethodniStatus.isBlank()) {
            log.error("[CHOREOGRAPHY] sagaId={} -- BookCreationFailedEvent ne sadrzi prethodniStatus, kompenzacija nije moguca za narudzbinaid={}", event.getSagaId(), event.getNarudzbinaid());
            return;
        }

        if ("NONE".equals(prethodniStatus)) {
            // Korak 1 je bio prvi event uopste za ovu narudzbinu -- nema na sta da se vrati,
            // pa kompenzacija ovde znaci samo audit zapis da je SAGA zavrsena neuspehom.
            log.warn("[CHOREOGRAPHY] sagaId={} -- narudzbinaid={} nema prethodni status (NONE), kompenzacija se svodi na audit log", event.getSagaId(), event.getNarudzbinaid());
            objaviKompenzaciju(event, prethodniStatus);
            return;
        }

        // Uzimamo najnoviji upis kako bismo iz njega preuzeli sve potrebne tagove/fieldove
        // (dobavljacid, dobavljacnaziv, vrednostNarudzbine, brojStavki...) -- jedino noviStatus
        // i timestamp se mejaju, ostatak konteksta narudzbine ostaje isti.
        List<PromenaStatusaPorudzbine> poslednjiUpisi = repository.findLastStatusByNarudzbinaid(event.getNarudzbinaid());

        if (poslednjiUpisi.isEmpty()) {
            log.error("[CHOREOGRAPHY] sagaId={} -- nije pronadjen nijedan upis za narudzbinaid={}, kompenzacija nije moguca", event.getSagaId(), event.getNarudzbinaid());
            return;
        }

        PromenaStatusaPorudzbine korektivniZapis = poslednjiUpisi.get(0);
        korektivniZapis.setPrethodniStatus(korektivniZapis.getNoviStatus());
        korektivniZapis.setNoviStatus(prethodniStatus);
        korektivniZapis.setTimestamp(Instant.now());

        try {
            repository.saveStatusPromena(korektivniZapis);
            log.info("[CHOREOGRAPHY] sagaId={} -- kompenzacija uspesna, narudzbinaid={} vracen na noviStatus={}", event.getSagaId(), event.getNarudzbinaid(), prethodniStatus);

            objaviKompenzaciju(event, prethodniStatus);
        } catch (Exception e) {
            log.error("[CHOREOGRAPHY] sagaId={} -- GRESKA prilikom kompenzacije za narudzbinaid={}: {}", event.getSagaId(), event.getNarudzbinaid(), e.getMessage(), e);
        }
    }

    private void objaviKompenzaciju(BookCreationFailedEvent event, String vracenNaStatus) {
        OrderStatusCompensatedEvent compensated = new OrderStatusCompensatedEvent(
                event.getSagaId(),
                event.getNarudzbinaid(),
                vracenNaStatus,
                LocalDateTime.now());

        rabbitTemplate.convertAndSend(
                RabbitMQConfig.CHOREOGRAPHY_EXCHANGE,
                RabbitMQConfig.ORDERSTATUS_COMPENSATED_KEY,
                compensated);
        log.info("[CHOREOGRAPHY] sagaId={} -- OrderStatusCompensatedEvent objavljen", event.getSagaId());
    }
}