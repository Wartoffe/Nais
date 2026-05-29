package nais.ColumnarDBService.repository;

import nais.ColumnarDBService.entity.ReturnByDate;
import org.springframework.data.cassandra.repository.CassandraRepository;
import org.springframework.data.cassandra.repository.Query;
import org.springframework.stereotype.Repository;
import java.util.List;
@Repository
public interface ReturnByDateRepository extends CassandraRepository<ReturnByDate, String> {

    //sva vracanja za odredjeni datum
    @Query("SELECT * FROM returns_by_date WHERE return_date = ?0")
    List<ReturnByDate> findByReturnDate(String returnDate);

    //broj vracanja knjiga na odredjeni datum
    @Query("SELECT COUNT(*) FROM returns_by_date WHERE return_date = ?0")
    Long countByReturnDate(String returnDate);
}
