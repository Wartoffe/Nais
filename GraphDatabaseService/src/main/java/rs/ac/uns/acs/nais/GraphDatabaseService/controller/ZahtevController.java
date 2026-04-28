package rs.ac.uns.acs.nais.GraphDatabaseService.controller;

import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.nais.GraphDatabaseService.dto.ZahtevDTO;
import rs.ac.uns.acs.nais.GraphDatabaseService.service.ZahtevService;

import java.util.List;

@RestController
@RequestMapping("/api/zahtevi")
public class ZahtevController {

    private final ZahtevService service;

    public ZahtevController(ZahtevService service) {
        this.service = service;
    }

    //GRANA "ZAINTERESOVAN ZA" CREATE
    @PostMapping
    public void dodajZahtev(@RequestParam String email,
                            @RequestParam String isbn) {
        service.dodajZahtev(email, isbn);
    }

    //GRANA "ZAINTERESOVAN ZA" DELETE
    @DeleteMapping
    public void obrisiZahtev(@RequestParam String email,
                             @RequestParam String isbn) {
        service.obrisiZahtev(email, isbn);
    }

    //GRANA "ZAINTERESOVAN ZA" READ
    @GetMapping("/{email}")
    public List<ZahtevDTO> getZahtevi(@PathVariable String email) {
        return service.getZahtevi(email);
    }

    //nije mi imalo smisla da radim apdejt nez
}
