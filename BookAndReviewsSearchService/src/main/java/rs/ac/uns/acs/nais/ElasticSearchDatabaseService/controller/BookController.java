package rs.ac.uns.acs.nais.ElasticSearchDatabaseService.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.nais.ElasticSearchDatabaseService.model.Book;
import rs.ac.uns.acs.nais.ElasticSearchDatabaseService.service.impl.BookService;

import java.util.List;

/**
 * REST controller for book search and management backed by Elasticsearch.
 * Base path: /books
 * Exposes a range of full-text search strategies over the books index.
 *  * ┌─────────────────────────────────────────────────────────────────────────┐
 *  * │ CRUD Method │       Path        │  Description                          │
 *  * ├─────────────────────────────────────────────────────────────────────────┤
 *  * │  POST       │  /books           │  Create 1 book                        │
 *  * │  POST       │  /books/batch     │  Create N books                       │
 *  * │  GET        │  /books/{id}      │  Get 1 book by ID                     │
 *  * │  GET        │  /books           │  Get all books                        │
 *  * │  GET        │  /books/batch     │  Get books by ID list                 │
 *  * │  PUT        │  /books/{id}      │  Update 1 book                        │
 *  * │  DELETE     │  /books/{id}      │  Delete 1 book                        │
 *  * │  DELETE     │  /books/batch     │  Delete books by ID list              │
 *  * └─────────────────────────────────────────────────────────────────────────┘
 */
@RestController
@RequestMapping("/books")
public class BookController {
    private final BookService bookService;

    public BookController(BookService bookService) {
        this.bookService = bookService;
    }

    // CREATE
    @PostMapping
    public ResponseEntity<Book> addBook(@RequestBody Book book) {
        Book saved = bookService.save(book);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }

    @PostMapping("/batch")
    public ResponseEntity<List<Book>> addBooks(@RequestBody List<Book> books) {
        List<Book> saved = bookService.saveAll(books);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }

    // UPDATE
    @PutMapping("/{id}")
    public ResponseEntity<Book> updateBook(@PathVariable String id, @RequestBody Book book) {
        try {
            Book updated = bookService.update(id, book);
            return ResponseEntity.ok(updated);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    // DELETE
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteBook(@PathVariable String id) {
        bookService.deleteById(id);
        return ResponseEntity.noContent().build();
    }

    @DeleteMapping("/batch")
    public ResponseEntity<Void> deleteBooks(@RequestBody List<String> ids) {
        bookService.deleteAllById(ids);
        return ResponseEntity.noContent().build();
    }

    // READ
    @GetMapping("/{id}")
    public ResponseEntity<Book> getBook(@PathVariable String id) {
        return bookService.findById(id).map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
    }

    @GetMapping
    public ResponseEntity<List<Book>> getAllBooks() {
        List<Book> books = bookService.findAll();
        return ResponseEntity.ok(books);
    }

    @GetMapping("/batch")
    public ResponseEntity<List<Book>> getBooksByIds(@RequestParam List<String> ids) {
        List<Book> books = bookService.findAllById(ids);
        return ResponseEntity.ok(books);
    }
}
