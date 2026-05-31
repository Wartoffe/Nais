package nais.ColumnarDBService.controller;

import nais.ColumnarDBService.dto.BookDTO;
import nais.ColumnarDBService.service.BookService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/books")
public class BookController {

    @Autowired
    private BookService bookService;
    @PostMapping
    public ResponseEntity<BookDTO> createBook(@RequestBody BookDTO dto) {
        return new ResponseEntity<>(bookService.createBook(dto), HttpStatus.CREATED);
    }
    @GetMapping
    public ResponseEntity<List<BookDTO>> getBooksByGenre(@RequestParam String genre) {
        return ResponseEntity.ok(bookService.getBooksByGenre(genre));
    }
    @GetMapping("/genre/{genre}/count")
    public ResponseEntity<Long> countBooksByGenre(@PathVariable String genre) {
        return ResponseEntity.ok(bookService.countBooksByGenre(genre));
    }

    @PutMapping
    public ResponseEntity<BookDTO> updateBook(@RequestBody BookDTO dto) {
        return ResponseEntity.ok(bookService.updateBook(dto));
    }
    @DeleteMapping("/{genre}/{title}/{bookId}")
    public ResponseEntity<Void> deleteBook(@PathVariable String genre,
                                           @PathVariable String title,
                                           @PathVariable UUID bookId) {
        bookService.deleteBook(genre, title, bookId);
        return ResponseEntity.noContent().build();
    }

}
