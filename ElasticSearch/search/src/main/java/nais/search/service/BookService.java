package nais.search.service;

import nais.search.dto.BookDto;
import nais.search.model.Book;
import nais.search.repository.BookRepository;
import org.springframework.data.domain.Page;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class BookService {

    private final BookRepository bookRepository;

    public BookService(BookRepository bookRepository) {
        this.bookRepository = bookRepository;
    }

    public Optional<Book> getBookByRecordId(String recordId){
        return bookRepository.findByRecordId(recordId);
    }

    public Book createNewBook(Book book){
        return bookRepository.save(book);
    }

    public Book updateBook(String recordId, Book book){
        Book targetBook = bookRepository.findByRecordId(recordId).get();
        targetBook = book;
        return bookRepository.save(targetBook);
    }

    public boolean deleteBook(String recordId){
        bookRepository.deleteById(recordId);
        return true;
    }

    public Page<Book> fullTextSearch(){
        return null;
    }

    public Page<Book> filteredKeywordSearch(){
        return null;
    }
}
