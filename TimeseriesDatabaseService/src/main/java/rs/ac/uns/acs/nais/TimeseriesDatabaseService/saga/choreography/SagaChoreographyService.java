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
import java.util.List;
import java.util.UUID;

/*
 * Ulazna tacka za samu koreografisanu SAGA. Detaljan tok je objasnjen u kontroleru koji poziva ovaj servis.
 */
@Slf4j
@Service
public class SagaChoreographyService {
    // Status koji koristimo kao "prethodni" kada za datu narudzbinu jos ne postoji nijedan upisan event (prvi event uopste za tu narudzbinu)
    private static final String NEMA_PRETHODNOG_STATUSA = "NONE";
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

        String narudzbinaid = zahtev.getPromenaStatusaPorudzbine().getNarudzbinaid();

        // Cuvamo staro stanje u slucaju greske (rollback) i kako bismo ga prosledili dalje kroz event lanac (potrebno kasnijoj kompenzaciji ako VectorDatabaseService padne).
        // NAPOMENA: ako za ovu narudzbinu jos ne postoji nijedan upisan event (prvi event uopste),  lista ce biti praznja - tada nema prethodnog stanja na koje bismo se vratili.
        List<PromenaStatusaPorudzbine> poslednjiUpisi = repository.findLastStatusByNarudzbinaid(narudzbinaid);
        PromenaStatusaPorudzbine staroStanje = poslednjiUpisi.isEmpty() ? null : poslednjiUpisi.get(0);
        String prethodniStatus = staroStanje != null ? staroStanje.getNoviStatus() : NEMA_PRETHODNOG_STATUSA;

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
                narudzbinaid,
                prethodniStatus,
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
            log.error("[CHOREOGRAPHY] sagaId={} -- GRESKA prilikom objave ChangeOfOrderStatusCreateEvent: {}", sagaId, e.getMessage(), e);

            if (staroStanje == null) {
                // Nije postojalo prethodno stanje (ovo je bio prvi event za narudzbinu).
                log.warn("[CHOREOGRAPHY] sagaId={} -- nema prethodnog stanja za narudzbinaid={}, rollback Koraka 1 nije moguc", sagaId, narudzbinaid);
            } else {
                // RabbitMQ dostava nije prosla, dakle upisujemo korektivni zapis koji vraca staro stanje
                log.warn("[CHOREOGRAPHY] sagaId={} -- vracamo staro stanje zbog greske", sagaId);
                staroStanje.setTimestamp(Instant.now());
                repository.saveStatusPromena(staroStanje);
            }
            throw new RuntimeException("RabbitMQ dostava nije prosla za sagaId=" + sagaId, e);
        }

        return sagaId;
    }
}
