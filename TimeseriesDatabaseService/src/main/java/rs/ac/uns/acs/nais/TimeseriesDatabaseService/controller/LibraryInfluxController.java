package rs.ac.uns.acs.nais.TimeseriesDatabaseService.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.dto.UnosKnjigaIPromenaStatusaPorudzbineDTO;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaBudzetaPoZanru;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaPredlogaZaNabavku;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaStatusaPorudzbine;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.SagaChoreographyService;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.service.LibraryInfluxService;

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/library-influx")
public class LibraryInfluxController {

    private final LibraryInfluxService service;

    private final SagaChoreographyService sagaChoreographyService;

    public LibraryInfluxController(LibraryInfluxService service, SagaChoreographyService sagaChoreographyService) {
        this.service = service;
        this.sagaChoreographyService = sagaChoreographyService;
    }

    // PromenaStatusaPorudzbine
    // ===============================================================


    //CREATE — upisuje jedan event promene statusa narudžbine.
    @PostMapping("/status-promene/save")
    public ResponseEntity<Boolean> saveStatusPromena(@RequestBody PromenaStatusaPorudzbine m) {
        if (service.saveStatusPromena(m)) {
            return new ResponseEntity<>(true, HttpStatus.OK);
        } else {
            return new ResponseEntity<>(false, HttpStatus.BAD_REQUEST);
        }
    }

    // Koreografisana SAGA
    /* Zapocinje koregorafisani SAGA sablon za unos knjige koja je stigla porudzbinom i u vektorsku bazu za AI asistenta.
     * Tok:
     * 1. Upisuje se novi event statusa porudzbine.
     * 2. Servis nad vektorskom bazom slusa i hvata event, nakon cega radi unos nove knjige i kreiranje vector embedding-a,
     * 3. U slucaju da taj servis padne, objavljuje BookCreationFailedEvent.
     * 4. CompensationListener slusa u slucaju objave i vraca prethodno aktivni status porudzbine (delete se ne radi u timeseries).
     *
     * @param request body koji sadrzi podatke o promeni statusa porudzbine, ali i o knjigama koje u njemu ucestvuju
     * @return sagaId novokreirane SAGA instance
     */
    @PostMapping("/status-promene/save/saga")
    public ResponseEntity<Map<String, String>> saveStatusPromenaSaga(@RequestBody UnosKnjigaIPromenaStatusaPorudzbineDTO zahtev) {
        log.info("[CONTROLLER] POST /library-influx/status-promene/save/saga -- koreografisana saga -- zahtev: {}", zahtev);

        try {
            String sagaId = sagaChoreographyService.saveStatusPromena(zahtev);

            log.info("[CONTROLLER] Koreografisana SAGA je pocela -- sagaId={}", sagaId);
            return ResponseEntity.ok(Map.of(
                    "sagaId", sagaId,
                    "status", "STARTED",
                    "message", "Koreografisana SAGA je pocela. Pratite logove za detalje."));

        } catch (Exception e) {
            log.error("[CONTROLLER] GRESKA kod pokreanja koreografisane SAGA: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage()));
        }
    }

    //READ — kompletan lifecycle jedne narudžbine.
    @GetMapping("/status-promene/findByNarudzbina")
    public ResponseEntity<List<PromenaStatusaPorudzbine>> findStatusByNarudzbinaid(
            @RequestParam String narudzbinaid) {
        return new ResponseEntity<>(service.findStatusByNarudzbinaid(narudzbinaid), HttpStatus.OK);
    }


    //READ — svi eventi određenog statusa u poslednjih N dana.
    @GetMapping("/status-promene/findByStatus")
    public ResponseEntity<List<PromenaStatusaPorudzbine>> findStatusByNoviStatus(
            @RequestParam String noviStatus,
            @RequestParam(defaultValue = "30") int days) {
        return new ResponseEntity<>(service.findStatusByNoviStatus(noviStatus, days), HttpStatus.OK);
    }



    // PromenaBudzetaPoZanru
    // ==================================================================

    //CREATE — upisuje promenu budžeta za žanr.
    @PostMapping("/budzet-promene/save")
    public ResponseEntity<Boolean> saveBudzetPromena(@RequestBody PromenaBudzetaPoZanru m) {
        if (service.saveBudzetPromena(m)) {
            return new ResponseEntity<>(true, HttpStatus.OK);
        } else {
            return new ResponseEntity<>(false, HttpStatus.BAD_REQUEST);
        }
    }

    // READ — sve promene budžeta za dati žanr.
    @GetMapping("/budzet-promene/findByZanr")
    public ResponseEntity<List<PromenaBudzetaPoZanru>> findBudzetByZanr(@RequestParam String zanr) {
        return new ResponseEntity<>(service.findBudzetByZanr(zanr), HttpStatus.OK);
    }

    //READ — sve promene određenog tipa (NABAVKA / POVRACAJ / KOREKCIJA_BUDZETA).
    @GetMapping("/budzet-promene/findByTip")
    public ResponseEntity<List<PromenaBudzetaPoZanru>> findBudzetByTipPromene(
            @RequestParam String tipPromene) {
        return new ResponseEntity<>(service.findBudzetByTipPromene(tipPromene), HttpStatus.OK);
    }



    // PromenaPredlogaZaNabavku
    // ================================================================

    //CREATE — upisuje promenu statusa predloga za nabavku.
    @PostMapping("/predlog-promene/save")
    public ResponseEntity<Boolean> savePredlogPromena(@RequestBody PromenaPredlogaZaNabavku m) {
        if (service.savePredlogPromena(m)) {
            return new ResponseEntity<>(true, HttpStatus.OK);
        } else {
            return new ResponseEntity<>(false, HttpStatus.BAD_REQUEST);
        }
    }

    //READ — lifecycle jednog predloga.
    @GetMapping("/predlog-promene/findByPredlog")
    public ResponseEntity<List<PromenaPredlogaZaNabavku>> findPredlogByPredlogid(
            @RequestParam String predlogid) {
        return new ResponseEntity<>(service.findPredlogByPredlogid(predlogid), HttpStatus.OK);
    }

    //READ — svi predlozi za dati žanr.
    @GetMapping("/predlog-promene/findByZanr")
    public ResponseEntity<List<PromenaPredlogaZaNabavku>> findPredlogByZanr(@RequestParam String zanr) {
        return new ResponseEntity<>(service.findPredlogByZanr(zanr), HttpStatus.OK);
    }



    // Složeni upiti
    // ================================================================

    //Upit 1: Prosečno vreme isporuke po dobavljaču (POSLATA->ISPORUCENA).
    @GetMapping("/analytics/vreme-isporuke")
    public ResponseEntity<List<Map<String, Object>>> avgVremeIsporuke(
            @RequestParam(defaultValue = "90") int days) {
        return new ResponseEntity<>(service.avgVremeIsporukePoDobavclja(days), HttpStatus.OK);
    }

    //Upit 2: Dinamika trošenja budžeta po žanru, mesečno.
    @GetMapping("/analytics/budzet-mesecno")
    public ResponseEntity<List<Map<String, Object>>> budzetMesecno(
            @RequestParam(defaultValue = "12") int months) {
        return new ResponseEntity<>(service.budzetPoZanruMesecno(months), HttpStatus.OK);
    }

    //Upit 3: Procenat odobrenih predloga po žanru
    @GetMapping("/analytics/odobreni-predlozi")
    public ResponseEntity<List<Map<String, Object>>> odobreniPredlozi(
            @RequestParam(defaultValue = "365") int days) {
        return new ResponseEntity<>(service.odobreniPredloziPoZanru(days), HttpStatus.OK);
    }

    //Upit 4 : Analiza otkazivanja po dobavljaču.
    @GetMapping("/analytics/otkazivanje")
    public ResponseEntity<List<Map<String, Object>>> otkazivanje(
            @RequestParam(defaultValue = "180") int days) {
        return new ResponseEntity<>(service.otkazivanjePoDobavclja(days), HttpStatus.OK);
    }
}