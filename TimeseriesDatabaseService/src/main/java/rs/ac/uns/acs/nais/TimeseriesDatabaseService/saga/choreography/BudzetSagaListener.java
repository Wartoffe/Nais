package rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography;

import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.configuration.RabbitMQConfig;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaBudzetaPoZanru;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.repository.LibraryInfluxRepositoryImpl;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event.BookReturnedToSupplierEvent;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event.BudzetUpdateFailedEvent;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event.BudzetUpdatedEvent;

import java.time.LocalDateTime;
import java.util.List;

// Slusa BookReturnedToSupplierEvent
// Ako upis ne uspe, objavljuje se BudgetUpdateFailedEvent — BookAndReviewsSearchService
// ga sluša i kao kompenzaciju vraća obrisanu knjigu nazad u indeks.

@Slf4j
@Component
public class BudzetSagaListener {

    // Samo ako za žanr još nema nijednog zapisa u InfluxDB-u:
    private static final double PODRAZUMEVANI_UKUPNI_BUDZET = 50000.0;

    private final LibraryInfluxRepositoryImpl repository;
    private final RabbitTemplate rabbitTemplate;

    public BudzetSagaListener(LibraryInfluxRepositoryImpl repository, RabbitTemplate rabbitTemplate) {
        this.repository = repository;
        this.rabbitTemplate = rabbitTemplate;
    }

    @RabbitListener(queues = RabbitMQConfig.BOOK_RETURNED_TO_SUPPLIER_QUEUE)
    public void handleBookReturnedToSupplier(BookReturnedToSupplierEvent event) {
        log.info("[CHOREOGRAPHY] sagaId={} -- primljen BookReturnedToSupplierEvent za bookId={}, naslov={}",
                event.getSagaId(), event.getBookId(), event.getNaslovKnjige());

        String zanr = ZanrNormalizer.normalizuj(event.getZanr());
        double iznos = event.getIznosPovracaja() != null ? Math.abs(event.getIznosPovracaja()) : 0.0;

        try {
            List<PromenaBudzetaPoZanru> poslednji = repository.findLastBudzetByZanr(zanr);

            double prethodnoStanje = !poslednji.isEmpty() && poslednji.get(0).getRaspolozivoStanje() != null
                    ? poslednji.get(0).getRaspolozivoStanje() : 0.0;
            double ukupniBudzet = !poslednji.isEmpty() && poslednji.get(0).getUkupniBudzet() != null
                    ? poslednji.get(0).getUkupniBudzet() : PODRAZUMEVANI_UKUPNI_BUDZET;

            PromenaBudzetaPoZanru promena = new PromenaBudzetaPoZanru();
            promena.setZanr(zanr);
            promena.setTipPromene("POVRACAJ");
            promena.setPromenaStanja(iznos);
            promena.setRaspolozivoStanje(prethodnoStanje + iznos);
            promena.setUkupniBudzet(ukupniBudzet);
            promena.setNapomena("Vraćena knjiga '" + event.getNaslovKnjige()
                    + "' (bookId=" + event.getBookId() + ") dobavljaču, sagaId=" + event.getSagaId());

            boolean uspesno = repository.saveBudzetPromena(promena);
            if (!uspesno) {
                throw new RuntimeException("InfluxDB write vratio false za saveBudzetPromena");
            }

            log.info("[CHOREOGRAPHY] sagaId={} -- budžet za žanr={} ažuriran, novo raspoloživo stanje={}",
                    event.getSagaId(), zanr, promena.getRaspolozivoStanje());

            BudzetUpdatedEvent uspeh = new BudzetUpdatedEvent(
                    event.getSagaId(), event.getBookId(), zanr, promena.getRaspolozivoStanje(), LocalDateTime.now());
            rabbitTemplate.convertAndSend(
                    RabbitMQConfig.CHOREOGRAPHY_EXCHANGE,
                    RabbitMQConfig.BUDGET_UPDATED_KEY,
                    uspeh);

        } catch (Exception e) {
            log.error("[CHOREOGRAPHY] sagaId={} -- GRESKA prilikom upisa POVRACAJ za bookId={}: {}",
                    event.getSagaId(), event.getBookId(), e.getMessage(), e);

            BudzetUpdateFailedEvent neuspeh = new BudzetUpdateFailedEvent(
                    event.getSagaId(), event.getBookId(), e.getMessage(), LocalDateTime.now());
            rabbitTemplate.convertAndSend(
                    RabbitMQConfig.CHOREOGRAPHY_EXCHANGE,
                    RabbitMQConfig.BUDGET_UPDATE_FAILED_KEY,
                    neuspeh);
        }
    }
}
