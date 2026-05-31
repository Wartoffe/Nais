package nais.ColumnarDBService.repository;

import nais.ColumnarDBService.entity.LoanByMember;
import org.springframework.data.cassandra.repository.CassandraRepository;
import org.springframework.data.cassandra.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface LoanByMemberRepository extends CassandraRepository<LoanByMember, UUID> {

    //sve pozajmice jednog clana
    @Query("SELECT * FROM loans_by_member WHERE member_id=?0")
    List<LoanByMember> findByMemberId(UUID memberId);

    // ukupan broj pozajmica clana - agregacija
    @Query("SELECT COUNT(*) FROM loans_by_member WHERE member_id = ?0")
    Long countByMemberId(UUID memberId);

    //prosecno trajanje pozajmica za nekog clana u danima - agregacija
    @Query("SELECT AVG(loan_duration_days) FROM loans_by_member " +
            "WHERE member_id = ?0 AND is_returned = true ALLOW FILTERING")
    Double avgLoanDurationByMember(UUID memberId);

    // nevracene pozajmice jednog clana
    @Query("SELECT * FROM loans_by_member WHERE member_id = ?0 AND is_returned = false ALLOW FILTERING")
    List<LoanByMember> findActiveLoansByMember(UUID memberId);
    @Query("DELETE FROM loans_by_member WHERE member_id = ?0 AND loan_date = ?1 AND loan_id = ?2")
    void deleteLoan(UUID memberId, LocalDateTime loanDate, UUID loanId);


}
