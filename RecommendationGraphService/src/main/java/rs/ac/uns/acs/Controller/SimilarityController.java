package rs.ac.uns.acs.Controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.Model.Book;
import rs.ac.uns.acs.Model.Similar;
import rs.ac.uns.acs.Service.SimilarityService;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/similar-to")
public class SimilarityController {
    private final SimilarityService similarToService;

    public SimilarityController(SimilarityService similarityService){
        this.similarToService=similarityService;
    }
    @PostMapping("/book/{bookId}/target/{targetBookId}")
    public ResponseEntity<Book> add(
            @PathVariable String bookId,
            @PathVariable String targetBookId,
            @RequestBody Map<String, Double> body) {
        double score = body.get("score");
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(similarToService.add(bookId, targetBookId, score));
    }
    @GetMapping("/book/{bookId}")
    public ResponseEntity<List<Similar>> readAll(@PathVariable String bookId) {
        return ResponseEntity.ok(similarToService.readAll(bookId));
    }
    @PutMapping("/book/{bookId}/target/{targetBookId}")
    public ResponseEntity<Void> updateScore(
            @PathVariable String bookId,
            @PathVariable String targetBookId,
            @RequestBody Map<String, Double> body) {

        double newScore = body.get("score");
        similarToService.updateScore(bookId, targetBookId, newScore);

        return ResponseEntity.ok().build();
    }
    @DeleteMapping("/book/{bookId}/target/{targetBookId}")
    public ResponseEntity<Book> remove(
            @PathVariable String bookId,
            @PathVariable String targetBookId) {
        return ResponseEntity.ok(similarToService.remove(bookId, targetBookId));
    }

}
