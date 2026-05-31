package nais.ColumnarDBService.repository;

import nais.ColumnarDBService.entity.BookByGenre;
import org.springframework.data.cassandra.repository.CassandraRepository;
import org.springframework.data.cassandra.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface BookByGenreRepository extends CassandraRepository<BookByGenre, String> {

    //sve knjige nekog zanra
    @Query("SELECT * FROM books_by_genre WHERE genre = ?0")
    List<BookByGenre> findByGenre(String genre);

    //broj knjiga u datom zanru
    @Query("SELECT COUNT(*) FROM books_by_genre WHERE genre = ?0")
    Long countByGenre(String genre);
    @Query("DELETE FROM books_by_genre WHERE genre = ?0 AND title = ?1 AND book_id = ?2")
    void deleteBook(String genre, String title, UUID bookId);
}
