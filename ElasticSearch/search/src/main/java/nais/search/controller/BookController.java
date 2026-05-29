package nais.search.controller;

import nais.search.model.Book;
import nais.search.service.BookService;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("api/books")
public class BookController {

    private final BookService bookService;

    public BookController(BookService bookService) {
        this.bookService = bookService;
    }

    @GetMapping("/books_text/{recordId}") //TextIdx
    public Book getBookText(){}

    @PostMapping("/books_text/create") //TextIdx
    public ResponseEntity<?> newBookText(){}

    @PatchMapping("/books_text/{recordId}") //TextIdx
    public ResponseEntity<?> updateBookText(){}

    @DeleteMapping("/books_text/{recordId}") //TextIdx
    public ResponseEntity<?> deleteBookText(){}

    @GetMapping("/books_keyword/{recordId}") //KeywordIdx
    public Book getBookKeyword(){}

    @PostMapping("/books_keyword/create") //KeywordIdx
    public ResponseEntity<?> newBookKeyword(){}

    @PatchMapping("/books_keyword/{recordId}") //KeywordIdx
    public ResponseEntity<?> updateBookKeyword(){}

    @DeleteMapping("/books_keyword/{recordId}") //KeywordIdx
    public ResponseEntity<?> deleteBookKeyword(){}

    @GetMapping("/fulltext-search") //Q1 TextIdxOnly
    public Page<Book> getBooksByText(){

    }

    @GetMapping("/keyword-search") //Q2 KeywordIdxOnly
    public Page<Book> getBooksByKeyword(){

    }

    @GetMapping("/hybrid-search") //Q3 Hybrid
    public Page<Book> getBooksByHybrid(){

    }
}
