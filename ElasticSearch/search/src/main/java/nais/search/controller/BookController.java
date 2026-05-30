package nais.search.controller;

import nais.search.dto.BookDto;
import nais.search.model.Book;
import nais.search.service.BookService;
import nais.search.enums.Format;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Optional;

@RestController
@RequestMapping("/api/books")
public class BookController {

    private final BookService bookService;

    public BookController(BookService bookService) {
        this.bookService = bookService;
    }

    @GetMapping("/{recordId}")
    public Optional<Book> getBookById(@PathVariable String recordId) {
        Optional<Book> book = bookService.getBookByRecordId(recordId);
        if (book.isEmpty())
            return Optional.empty();
        return book;
    }

    @PostMapping("/create")
    public ResponseEntity<?> newBook(@RequestBody BookDto bookDto) {
        Book book = new Book(bookDto);
        if (bookService.createNewBook(book) != null)
            return ResponseEntity.ok("Book added successfully");
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Failed to add book");
    }

    @PatchMapping("/{recordId}")
    public ResponseEntity<?> updateBookById(@PathVariable String recordId, @RequestBody BookDto bookDto) {
        Book updated = bookService.updateBook(recordId, bookDto);
        if (updated != null)
            return ResponseEntity.ok("Book updated successfully");
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Failed to update book: invalid id");
    }

    @DeleteMapping("/{recordId}")
    public ResponseEntity<?> deleteBookById(@PathVariable String recordId) {
        try {
            bookService.deleteBook(recordId);
            return ResponseEntity.ok("Book has been deleted successfully");
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Failed to delete book");
        }
    }

    @GetMapping("/fulltext-search")
    public Page<Book> fullTextSearch(
            @RequestParam String query,
            @PageableDefault(size = 20) Pageable pageable) {
        return bookService.fullTextSearch(query, pageable);
    }

    @GetMapping("/keyword-search")
    public Page<Book> keywordFilteredSearch(
            @RequestParam(required = false) String genre,
            @RequestParam(required = false) String language,
            @RequestParam(required = false) String publisher,
            @RequestParam(required = false) Format format,
            @RequestParam(required = false) String series,
            @RequestParam(required = false) String award,
            @RequestParam(required = false) String setting,
            @RequestParam(required = false) String character,
            @RequestParam(required = false) String isbn,
            @PageableDefault(size = 20) Pageable pageable) {
        return bookService.keywordFilteredSearch(
                genre, language, publisher, format,
                series, award, setting, character, isbn, pageable);
    }

    @GetMapping("/by-author-name")
    public Page<Book> authorNameSearch(
            @RequestParam(required = false) String firstName,
            @RequestParam(required = false) String lastName,
            @PageableDefault(size = 20) Pageable pageable) {
        return bookService.findBooksByAuthorName(firstName, lastName, pageable);
    }
}