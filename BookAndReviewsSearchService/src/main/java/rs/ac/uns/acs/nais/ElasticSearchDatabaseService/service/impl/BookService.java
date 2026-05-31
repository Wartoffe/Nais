package rs.ac.uns.acs.nais.ElasticSearchDatabaseService.service.impl;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.nais.ElasticSearchDatabaseService.model.Book;
import rs.ac.uns.acs.nais.ElasticSearchDatabaseService.repository.BookRepository;
import rs.ac.uns.acs.nais.ElasticSearchDatabaseService.service.IBookService;

import java.util.List;
import java.util.Optional;
import java.util.stream.StreamSupport;

/**
 * Service layer for book search and management backed by Elasticsearch.
 * Delegates all Elasticsearch interactions to BookRepository, which uses
 * Spring Data Elasticsearch and custom @Query annotations to build various
 * search strategies.
 */
@Service
public class BookService implements IBookService {
    private final BookRepository bookRepository;

    public BookService(BookRepository bookRepository) {
        this.bookRepository = bookRepository;
    }

    // CREATE
    @Override
    public Book save(Book book) {
        return bookRepository.save(book);
    }

    @Override
    public List<Book> saveAll(List<Book> books) {
        Iterable<Book> saved = bookRepository.saveAll(books);
        return StreamSupport.stream(saved.spliterator(), false).toList();
    }

    // UPDATE
    @Override
    public Book update(String id, Book book) {
        if (!bookRepository.existsById(id)) {
            throw new IllegalArgumentException("Book with ID '" + id + "' does not exist in index.");
        }
        book.setBookId(id);
        return bookRepository.save(book);
    }

    // DELETE
    @Override
    public void deleteById(String id) {
        bookRepository.deleteById(id);
    }

    @Override
    public void deleteAllById(List<String> ids) {
        bookRepository.deleteAllById(ids);
    }

    // READ
    @Override
    public Optional<Book> findById(String id) {
        return bookRepository.findById(id);
    }

    @Override
    public List<Book> findAll() {
        Iterable<Book> all = bookRepository.findAll();
        return StreamSupport.stream(all.spliterator(), false).toList();
    }

    @Override
    public List<Book> findAllById(List<String> ids) {
        Iterable<Book> found = bookRepository.findAllById(ids);
        return StreamSupport.stream(found.spliterator(), false).toList();
    }
}
