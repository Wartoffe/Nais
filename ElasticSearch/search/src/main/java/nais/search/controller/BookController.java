package nais.search.controller;

import nais.search.dto.BookDto;
import nais.search.model.Book;
import nais.search.service.BookService;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.RequestEntity;
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

    @GetMapping("/{recordId}") //TextIdx
    public Optional<Book> getBookById(@PathVariable String recordId){
        Optional<Book> book = bookService.getBookByRecordId(recordId);
        if(book.isEmpty())
            return Optional.empty();
        return book;
    }

    @PostMapping("/create") //TextIdx
    public ResponseEntity<?> newBook(@RequestBody BookDto bookDto){
        Book book = new Book(bookDto);
        if(bookService.createNewBook(book) != null)
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


    @DeleteMapping("/{recordId}") //TextIdx
    public ResponseEntity<?> deleteBookById(@PathVariable String recordId){
        try{
            bookService.deleteBook(recordId);
            return ResponseEntity.ok("Book has been deleted successfully");
        } catch (RuntimeException e){
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Failed to delete book");
        }
    }

    @GetMapping("/fulltext-search") //Q1 TextIdxOnly
    public Page<Book> fullTextSearch(){
        return null;
    }

    @GetMapping("/keyword-search") //Q2 KeywordIdxOnly
    public Page<Book> keywordFilteredSearch(){
        return null;
    }

    @GetMapping("/by-author-name") //Q3 byAuthorName
    public Page<Book> authorNameSearch(){ return null; }
}
