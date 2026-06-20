package rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography;

import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.configuration.RabbitMQConfig;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.dto.UnosKnjigaIPromenaStatusaPorudzbineDTO;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaStatusaPorudzbine;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.repository.LibraryInfluxRepositoryImpl;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event.ChangeOfOrderStatusCreatedEvent;

import java.time.Instant;
import java.time.LocalDateTime;
import java.util.UUID;

/*
 * Ulazna tacka za samu koreografisanu SAGA. Detaljan tok je objasnjen u kontroleru koji poziva ovaj servis.
 */
@Slf4j
@Service
public class SagaChoreographyService {
    private final LibraryInfluxRepositoryImpl repository;
    private final RabbitTemplate rabbitTemplate;

    public SagaChoreographyService(LibraryInfluxRepositoryImpl repository, RabbitTemplate rabbitTemplate) {
        this.repository = repository;
        this.rabbitTemplate = rabbitTemplate;
    }

    /*
     * Kreira upravo samu PromenuStatusaPorudzbine unutar Influx baze podataka i nakon uspesnog izvrsenja objavljuje ChangeOfOrderStatusCreatedEvent.
     * U slucaju da knjiga vec postoji u bazi, samo ce se preskociti i nastaviti dalje sa ostalima.
     *
     * @param zahtev tipa UnosKnjigaIPromenaStatusaPorudzbineDTO
     * @return sagaId kako bi se identifikovala saga instanca
     */
    public String saveStatusPromena(UnosKnjigaIPromenaStatusaPorudzbineDTO zahtev) {
        String sagaId = UUID.randomUUID().toString();
        log.info("[CHOREOGRAPHY] sagaId={} -- zahtev={}", sagaId, zahtev);

        // Cuvamo staro stanje u slucaju greske
        PromenaStatusaPorudzbine promenaStatusaPorudzbine = repository.findLastStatusByNarudzbinaid(zahtev.getPromenaStatusaPorudzbine().getNarudzbinaid()).getFirst();

        // Korak 1: Upis u Influx Timeseries bazu podataka
        try {
            repository.saveStatusPromena(zahtev.getPromenaStatusaPorudzbine());
            log.info("[CHOREOGRAPHY] sagaId={} -- Uspesan unos PromeneStatusaPorudzbine", sagaId);
        } catch (Exception e) {
            log.error("[CHOREOGRAPHY] sagaId={} -- GRESKA prilikom unosa PromenaStatusaPorudzbine: {}", sagaId, e.getMessage(), e);
            throw new RuntimeException("Neo4j write failed for sagaId=" + sagaId, e);
        }

        // Korak 2: Objavljivanje ChangeOfOrderStatusCreatedEvent koji ce biti uhvacen od strane servisa nad vektorskom bazom podataka
        ChangeOfOrderStatusCreatedEvent event = new ChangeOfOrderStatusCreatedEvent(
                sagaId,
                zahtev.getPromenaStatusaPorudzbine().getNarudzbinaid(),
                zahtev.getKnjige(),
                LocalDateTime.now());

        try {
            rabbitTemplate.convertAndSend(
                    RabbitMQConfig.CHOREOGRAPHY_EXCHANGE,
                    RabbitMQConfig.ORDERSTATUS_CREATED_KEY,
                    event);
            log.info("[CHOREOGRAPHY] sagaId={} -- ChangeOfOrderStatusCreateEvent objavljen na exchange={}, key={}",
                    sagaId, RabbitMQConfig.CHOREOGRAPHY_EXCHANGE, RabbitMQConfig.ORDERSTATUS_CREATED_KEY);
        } catch (Exception e) {
            log.error("[CHOREOGRAPHY] sagaId={} -- GRESKA prilikom objave ChangeOfOrderStatusCreateEvent: {}",
                    sagaId, e.getMessage(), e);
            // RabbitMQ dostava nije prosla, dakle upisujemo ponovo prethodno stanje
            log.warn("[CHOREOGRAPHY] sagaId={} -- vracamo staro stanje zbog greske", sagaId);
            promenaStatusaPorudzbine.setTimestamp(Instant.now());
            repository.saveStatusPromena(promenaStatusaPorudzbine);
            throw new RuntimeException("RabbitMQ dostava nije prosla za sagaId=" + sagaId, e);
        }

        return sagaId;
    }
}
