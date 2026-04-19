package rs.ac.uns.acs.Service;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.Model.Book;
import rs.ac.uns.acs.Repository.BookRepository;

import java.util.List;

@Service
public class BookService {
    private final BookRepository bookRepository;

    public BookService(BookRepository bookRepository){
        this.bookRepository=bookRepository;
    }
    public void addGenreToBook(String bookId, Long genreId){
        bookRepository.addGenreToBook(bookId, genreId);
    }
    public void createSimilarity(){
        bookRepository.createSimilarityByGenre();
    }

    public List<Book> recommendByGenre(Long memberId){
        return bookRepository. recommendByGenre(memberId);
    }

    public List<Book> recommendBySimilarity(Long memberId){
        return bookRepository.recommendBySimilarity(memberId);
    }
}
