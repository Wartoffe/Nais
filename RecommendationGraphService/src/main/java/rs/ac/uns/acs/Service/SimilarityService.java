package rs.ac.uns.acs.Service;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.Model.Book;
import rs.ac.uns.acs.Model.Similar;
import rs.ac.uns.acs.Repository.BookRepository;

import java.util.List;

@Service
public class SimilarityService {
    private final BookRepository bookRepository;
    public SimilarityService(BookRepository bookRepository){
        this.bookRepository=bookRepository;
    }
    private Book findBook(String id) {
        return bookRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Book not found: " + id));
    }
    public Book add(String bookId, String targetBookId, double score) {
        Book book = findBook(bookId);
        Book target = findBook(targetBookId);

        boolean alreadyLinked = book.getSimilarBooks().stream()
                .anyMatch(s -> s.getBook().getId().equals(targetBookId));
        if (alreadyLinked) {
            throw new RuntimeException("SIMILAR_TO relationship already exists between "
                    + bookId + " and " + targetBookId);
        }

        Similar s1 = new Similar();
        s1.setBook(target);
        s1.setScore(score);

        Similar s2 = new Similar();
        s2.setBook(book);
        s2.setScore(score);

        book.getSimilarBooks().add(s1);
        target.getSimilarBooks().add(s2);

        bookRepository.save(book);
        bookRepository.save(target);

        return book;
    }
    public List<Similar> readAll(String bookId) {
        return findBook(bookId).getSimilarBooks();
    }
    public Book updateScore(String bookId, String targetBookId, double newScore) {
        Book book = findBook(bookId);
        Similar similar = book.getSimilarBooks().stream()
                .filter(s -> s.getBook().getId().equals(targetBookId))
                .findFirst()
                .orElseThrow(() -> new RuntimeException(
                        "No SIMILAR_TO relationship between " + bookId + " and " + targetBookId));
        similar.setScore(newScore);
        return bookRepository.save(book);
    }
    public Book remove(String bookId, String targetBookId) {
        bookRepository.deleteSimilarBothDirections(bookId, targetBookId);
        return findBook(bookId);
    }

}
