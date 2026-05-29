package nais.ColumnarDBService.repository;

import nais.ColumnarDBService.entity.LoanByBook;
import org.springframework.data.cassandra.repository.CassandraRepository;
import org.springframework.data.cassandra.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface LoanByBookRepository extends CassandraRepository<LoanByBook, UUID> {

    //istorija pozajmica za datu knjigu
    @Query("SELECT * FROM loans_by_book WHERE book_id = ?0")
    List<LoanByBook> findByBookId(UUID bookId);

    //koliko je puta knjiga bila pozajmljina-agregacija
    @Query("SELECT COUNT(*) FROM loans_by_book WHERE book_id = ?0")
    Long countByBookId(UUID bookId);
    @Query("DELETE FROM loans_by_book WHERE book_id = ?0 AND loan_date = ?1 AND loan_id = ?2")
    void deleteLoan(UUID bookId, LocalDateTime loanDate, UUID loanId);

}
