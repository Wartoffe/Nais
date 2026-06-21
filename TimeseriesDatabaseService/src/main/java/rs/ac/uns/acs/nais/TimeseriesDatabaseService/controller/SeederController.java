package rs.ac.uns.acs.nais.TimeseriesDatabaseService.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.service.DataSeederService;

/**
 * Kontroler za punjenje baze test podacima
 * kako ne bih morala kao u njihovom projektu
 * ručno da unosim svaki podatak sto je glupo
 * POST /library-influx/seed/all       — puni sva 3 merenja
 * POST /library-influx/seed/status    — samo PromenaStatusaPorudzbine
 * POST /library-influx/seed/budzet    — samo PromenaBudzetaPoZanru
 * POST /library-influx/seed/predlozi  — samo PromenaPredlogaZaNabavku
 */
@RestController
@RequestMapping("/library-influx/seed")
public class SeederController {

    private final DataSeederService seederService;

    public SeederController(DataSeederService seederService) {
        this.seederService = seederService;
    }

    @PostMapping("/all")
    public ResponseEntity<String> seedAll() {
        return new ResponseEntity<>(seederService.seedAll(), HttpStatus.OK);
    }

    @PostMapping("/status")
    public ResponseEntity<String> seedStatus() {
        int n = seederService.seedStatusPromene();
        return new ResponseEntity<>("PromenaStatusaPorudzbine: " + n + " slogova upisano.", HttpStatus.OK);
    }

    @PostMapping("/budzet")
    public ResponseEntity<String> seedBudzet() {
        int n = seederService.seedBudzetPromene();
        return new ResponseEntity<>("PromenaBudzetaPoZanru: " + n + " slogova upisano.", HttpStatus.OK);
    }

    @PostMapping("/predlozi")
    public ResponseEntity<String> seedPredlozi() {
        int n = seederService.seedPredlogPromene();
        return new ResponseEntity<>("PromenaPredlogaZaNabavku: " + n + " slogova upisano.", HttpStatus.OK);
    }
}
