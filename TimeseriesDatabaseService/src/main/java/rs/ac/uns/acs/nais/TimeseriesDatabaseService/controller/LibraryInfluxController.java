package rs.ac.uns.acs.nais.TimeseriesDatabaseService.controller;

import com.influxdb.query.FluxRecord;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaBudzetaPoZanru;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaPredlogaZaNabavku;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaStatusaPorudzbine;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.service.LibraryInfluxService;

import java.util.List;

@RestController
@RequestMapping("/library-influx")
public class LibraryInfluxController {

    private final LibraryInfluxService service;

    public LibraryInfluxController(LibraryInfluxService service) {
        this.service = service;
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
    public ResponseEntity<List<FluxRecord>> avgVremeIsporuke(
            @RequestParam(defaultValue = "90") int days) {
        return new ResponseEntity<>(service.avgVremeIsporukePoDobavclja(days), HttpStatus.OK);
    }

    //Upit 2: Dinamika trošenja budžeta po žanru, mesečno.
    @GetMapping("/analytics/budzet-mesecno")
    public ResponseEntity<List<FluxRecord>> budzetMesecno(
            @RequestParam(defaultValue = "12") int months) {
        return new ResponseEntity<>(service.budzetPoZanruMesecno(months), HttpStatus.OK);
    }

    //Upit 3: Procenat odobrenih predloga po žanru
    @GetMapping("/analytics/odobreni-predlozi")
    public ResponseEntity<List<FluxRecord>> odobreniPredlozi(
            @RequestParam(defaultValue = "365") int days) {
        return new ResponseEntity<>(service.odobreniPredloziPoZanru(days), HttpStatus.OK);
    }

    //Upit 4 : Analiza otkazivanja po dobavljaču.
    @GetMapping("/analytics/otkazivanje")
    public ResponseEntity<List<FluxRecord>> otkazivanje(
            @RequestParam(defaultValue = "180") int days) {
        return new ResponseEntity<>(service.otkazivanjePoDobavclja(days), HttpStatus.OK);
    }
}