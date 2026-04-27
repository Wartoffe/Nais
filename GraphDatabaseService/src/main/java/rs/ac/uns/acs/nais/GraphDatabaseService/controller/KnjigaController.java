package rs.ac.uns.acs.nais.GraphDatabaseService.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Knjiga;
import rs.ac.uns.acs.nais.GraphDatabaseService.service.IKnjigaService;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/knjige")
public class KnjigaController {

    private final IKnjigaService knjigaService;

    public KnjigaController(IKnjigaService knjigaService) {
        this.knjigaService = knjigaService;
    }

    // READ
    @GetMapping
    public ResponseEntity<List<Knjiga>> findAll() {
        return ResponseEntity.ok(knjigaService.findAll());
    }

    // READ
    @GetMapping("/{isbn}")
    public ResponseEntity<Knjiga> findById(@PathVariable String isbn) {
        return ResponseEntity.ok(knjigaService.findById(isbn));
    }

    // CREATE
    @PostMapping
    public ResponseEntity<Knjiga> create(@RequestBody Knjiga knjiga) {
        return ResponseEntity.ok(knjigaService.create(knjiga));
    }

    // UPDATE
    @PutMapping("/{isbn}")
    public ResponseEntity<Knjiga> update(@PathVariable String isbn, @RequestBody Knjiga knjiga) {
        return ResponseEntity.ok(knjigaService.update(isbn, knjiga));
    }

    // DELETE
    @DeleteMapping("/{isbn}")
    public ResponseEntity<Void> delete(@PathVariable String isbn) {
        knjigaService.delete(isbn);
        return ResponseEntity.noContent().build();
    }
}
