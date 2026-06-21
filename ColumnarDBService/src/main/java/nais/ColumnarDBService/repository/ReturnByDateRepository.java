package nais.ColumnarDBService.repository;

import nais.ColumnarDBService.entity.ReturnByDate;
import org.springframework.data.cassandra.repository.CassandraRepository;
import org.springframework.data.cassandra.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface ReturnByDateRepository extends CassandraRepository<ReturnByDate, String> {

    //sva vracanja za odredjeni datum
    @Query("SELECT * FROM returns_by_date WHERE return_date = ?0")
    List<ReturnByDate> findByReturnDate(String returnDate);

    //broj vracanja knjiga na odredjeni datum
    @Query("SELECT COUNT(*) FROM returns_by_date WHERE return_date = ?0")
    Long countByReturnDate(String returnDate);

    // saga compensation: undo a returnBook by deleting the return record it created
    @Query("DELETE FROM returns_by_date WHERE return_date = ?0 AND return_timestamp = ?1 AND loan_id = ?2")
    void deleteReturn(String returnDate, LocalDateTime returnTimestamp, UUID loanId);
}
