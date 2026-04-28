package rs.ac.uns.acs.Service;

import jakarta.transaction.Transactional;
import org.springframework.stereotype.Service;
import rs.ac.uns.acs.Model.Author;
import rs.ac.uns.acs.Model.Book;
import rs.ac.uns.acs.Model.Genre;
import rs.ac.uns.acs.Model.Similar;
import rs.ac.uns.acs.Repository.AuthorRepository;
import rs.ac.uns.acs.Repository.BookRepository;
import rs.ac.uns.acs.Repository.GenreRepository;

import java.util.ArrayList;
import java.util.List;

@Service
public class BookService {
    private final BookRepository bookRepository;
    private final AuthorRepository authorRepository;
    private final GenreRepository genreRepository;
    public BookService(BookRepository bookRepository, AuthorRepository authorRepository, GenreRepository genreRepository) {

        this.bookRepository = bookRepository;
        this.authorRepository=authorRepository;
        this.genreRepository=genreRepository;
    }
    
    public void addGenreToBook(String bookId, Long genreId) {
        bookRepository.addGenreToBook(bookId, genreId);
    }



    public List<Book> recommendByGenre(Long memberId) {
        return bookRepository.recommendByGenre(memberId);
    }

    public List<Book> recommendBySimilarity(Long memberId) {
        return bookRepository.recommendBySimilarity(memberId);
    }

    public List<Book> recommendByAuthor(Long memberId) {
        return bookRepository.recommendByAuthor(memberId);
    }

    public List<Book> recommendCombined(Long memberId) {
        return bookRepository.recommendCombined(memberId);
    }

    public Book create(Book book) {
        return bookRepository.save(book);
    }

    public List<Book> findAll() {
        return bookRepository.findAll();
    }
    public Book findById(String id) {
        return bookRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Book not found with id: " + id));
    }
    public Book update(String id, Book updated) {
        Book existing = findById(id);
        existing.setTitle(updated.getTitle());
        if (updated.getGenre() != null && !updated.getGenre().isEmpty()) {
            existing.setGenre(updated.getGenre());
        }
        if (updated.getAuthor() != null) {
            existing.setAuthor(updated.getAuthor());
        }
        return bookRepository.save(existing);
    }
    public void delete(String id) {
        Book book = findById(id);
        bookRepository.delete(book);
    }
    public Book assignAuthor(String bookId, Long authorId) {
        Book book = findById(bookId);
        Author author = authorRepository.findById(authorId)
                .orElseThrow(() -> new RuntimeException("Author not found with id: " + authorId));
        book.setAuthor(author);
        return bookRepository.save(book);
    }

    public Book assignGenre(String bookId, Long genreId) {
        Book book = findById(bookId);
        Genre genre = genreRepository.findById(genreId)
                .orElseThrow(() -> new RuntimeException("Genre not found with id: " + genreId));
        if (book.getGenre() == null) {
            book.setGenre(new ArrayList<>());
        }

        boolean exists = book.getGenre().stream()
                .anyMatch(g -> g.getId().equals(genreId));
        return bookRepository.save(book);
    }

    public Book addSimilarBook(String bookId, String similarBookId, double score) {
        Book book = findById(bookId);
        Book similarBook = findById(similarBookId);

        Similar similar = new Similar();
        similar.setBook(similarBook);
        similar.setScore(score);

        book.getSimilarBooks().add(similar);
        return bookRepository.save(book);
    }
}
