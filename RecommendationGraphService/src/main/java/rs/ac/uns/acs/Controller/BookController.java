package rs.ac.uns.acs.Controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.Model.Book;
import rs.ac.uns.acs.Service.BookService;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/books")
public class BookController {
    private final BookService bookService;

    public BookController(BookService service) {
        this.bookService = service;
    }

    @GetMapping("/recommend/genre")
    public ResponseEntity<List<Book>> recommendByGenre(@RequestParam Long memberId) {
        return ResponseEntity.ok(bookService.recommendByGenre(memberId));
    }
    @GetMapping("/recommend/similarity")
    public ResponseEntity<List<Book>> recommendBySimilarity(@RequestParam Long memberId) {
        return ResponseEntity.ok(bookService.recommendBySimilarity(memberId));
    }
    @GetMapping("/recommend/author")
    public ResponseEntity<List<Book>> recommendAuthor(@RequestParam Long memberId){
        return ResponseEntity.ok(bookService.recommendByAuthor(memberId));
    }
    @GetMapping("/recommend/combined")
    public ResponseEntity<List<Book>> recommendCombined(@RequestParam Long memberId){
        return  ResponseEntity.ok(bookService.recommendCombined(memberId));
    }
    @PostMapping
    public ResponseEntity<Book> create(@RequestBody Book book) {
        return ResponseEntity.status(HttpStatus.CREATED).body(bookService.create(book));
    }

    @GetMapping
    public ResponseEntity<List<Book>> findAll() {
        return ResponseEntity.ok(bookService.findAll());
    }
    @PutMapping("/{id}")
    public ResponseEntity<Book> update(@PathVariable String id, @RequestBody Book book) {
        return ResponseEntity.ok(bookService.update(id, book));
    }
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable String id) {
        bookService.delete(id);
        return ResponseEntity.noContent().build();
    }
    @PutMapping("/{id}/author/{authorId}")
    public ResponseEntity<Book> assignAuthor(@PathVariable String id, @PathVariable Long authorId) {
        return ResponseEntity.ok(bookService.assignAuthor(id, authorId));
    }
    @PutMapping("/{id}/genre/{genreId}")
    public ResponseEntity<Void> assignGenre(@PathVariable String id, @PathVariable Long genreId) {
        bookService.addGenreToBook(id, genreId);
        return ResponseEntity.ok().build();
    }
    @PostMapping("/{id}/similar")
    public ResponseEntity<Book> addSimilarBook(
            @PathVariable String id,
            @RequestBody Map<String, Object> body) {
        String similarBookId = (String) body.get("similarBookId");
        double score = ((Number) body.get("score")).doubleValue();
        return ResponseEntity.ok(bookService.addSimilarBook(id, similarBookId, score));
    }

}
