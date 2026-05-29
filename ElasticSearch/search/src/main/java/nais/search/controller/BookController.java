package nais.search.controller;

import nais.search.model.Book;
import nais.search.service.BookService;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Optional;

@RestController
@RequestMapping("api/books")
public class BookController {

    private final BookService bookService;

    public BookController(BookService bookService) {
        this.bookService = bookService;
    }

    @GetMapping("/{recordId}") //TextIdx
    public Optional<Book> getBookById(){
        return null;
    }

    @PostMapping("/create") //TextIdx
    public ResponseEntity<?> newBook(){
        return null;
    }

    @PatchMapping("/{recordId}") //TextIdx
    public ResponseEntity<?> updateBookById(){
        return null;
    }

    @DeleteMapping("/{recordId}") //TextIdx
    public ResponseEntity<?> deleteBookById(){
        return null;
    }

    @GetMapping("/fulltext-search") //Q1 TextIdxOnly
    public Page<Book> fullTextSearch(){
        return null;
    }

    @GetMapping("/keyword-search") //Q2 KeywordIdxOnly
    public Page<Book> keywordFilteredSearch(){
        return null;
    }
}
