package rs.ac.uns.acs.nais.GraphDatabaseService.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Zanr;
import rs.ac.uns.acs.nais.GraphDatabaseService.service.ZanrService;

import java.util.List;

@RestController
@RequestMapping("/api/zanrovi")
public class ZanrController {

    private final ZanrService zanrService;

    public ZanrController(ZanrService zanrService) {
        this.zanrService = zanrService;
    }

    //READ
    @GetMapping
    public ResponseEntity<List<Zanr>> findAll() {
        return ResponseEntity.ok(zanrService.findAll());
    }

    //READ
    @GetMapping("/{naziv}")
    public ResponseEntity<Zanr> findById(@PathVariable String naziv) {
        return ResponseEntity.ok(zanrService.findById(naziv));
    }

    ///CREATE
    @PostMapping
    public ResponseEntity<Zanr> create(@RequestBody Zanr zanr) {
        return ResponseEntity.ok(zanrService.create(zanr));
    }

    // UPDATE
    @PutMapping("/{naziv}")
    public ResponseEntity<Zanr> azurirajOpis(
            @PathVariable String naziv,
            @RequestParam String opis) {
        return ResponseEntity.ok(zanrService.azurirajOpis(naziv, opis));
    }

    // DELETE
    @DeleteMapping("/{naziv}")
    public ResponseEntity<Void> delete(@PathVariable String naziv) {
        zanrService.delete(naziv);
        return ResponseEntity.noContent().build();
    }
}
