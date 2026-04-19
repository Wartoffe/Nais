package rs.ac.uns.acs.Controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.Model.Book;
import rs.ac.uns.acs.Service.BookService;

import java.util.List;

@RestController
@RequestMapping("/books")
public class BookController {
    private final BookService bookService;

    public BookController(BookService service) {
        this.bookService = service;
    }
    @PostMapping("/addGenre")
    public ResponseEntity addGenre(@RequestParam String bookId, @RequestParam Long genreId) {
        bookService.addGenreToBook(bookId, genreId);
        return ResponseEntity.ok().build();
    }
    @PostMapping("/similarity")
    public ResponseEntity createSimilarity() {
        bookService.createSimilarity();
        return ResponseEntity.ok().build();
    }
    @GetMapping("/recommend/genre")
    public ResponseEntity<List<Book>> recommendByGenre(@RequestParam Long memberId) {
        return ResponseEntity.ok(bookService.recommendByGenre(memberId));
    }
    @GetMapping("/recommend/similarity")
    public ResponseEntity<List<Book>> recommendBySimilarity(@RequestParam Long memberId) {
        return ResponseEntity.ok(bookService.recommendBySimilarity(memberId));
    }
}
