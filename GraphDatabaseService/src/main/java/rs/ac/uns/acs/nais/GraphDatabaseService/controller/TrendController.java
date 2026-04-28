package rs.ac.uns.acs.nais.GraphDatabaseService.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Trend;
import rs.ac.uns.acs.nais.GraphDatabaseService.service.TrendService;

import java.util.List;

@RestController
@RequestMapping("/api/trendovi")
public class TrendController {

    private final TrendService trendService;

    public TrendController(TrendService trendService) {
        this.trendService = trendService;
    }

    // READ
    @GetMapping
    public ResponseEntity<List<Trend>> findAll() {
        return ResponseEntity.ok(trendService.findAll());
    }

    // READ
    @GetMapping("/{naziv}")
    public ResponseEntity<Trend> findById(@PathVariable String naziv) {
        return ResponseEntity.ok(trendService.findById(naziv));
    }

    // CREATE
    @PostMapping
    public ResponseEntity<Trend> create(@RequestBody Trend trend) {
        return ResponseEntity.ok(trendService.create(trend));
    }

    // UPDATE
    @PutMapping("/{naziv}")
    public ResponseEntity<Trend> azuriraj(
            @PathVariable String naziv,
            @RequestParam Integer score,
            @RequestParam String period) {
        return ResponseEntity.ok(trendService.azuriraj(naziv, score, period));
    }

    // DELETE
    @DeleteMapping("/{naziv}")
    public ResponseEntity<Void> delete(@PathVariable String naziv) {
        trendService.delete(naziv);
        return ResponseEntity.noContent().build();
    }
}
