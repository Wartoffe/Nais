package nais.ColumnarDBService.repository;

import nais.ColumnarDBService.entity.Member;
import org.springframework.data.cassandra.repository.CassandraRepository;
import org.springframework.data.cassandra.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface MemberRepository extends CassandraRepository<Member, UUID> {

    @Query("SELECT * FROM members WHERE member_id= ?0")
    Optional<Member> findByMemberId(UUID memberId);

    @Query("SELECT * FROM members")
    List<Member> findAllMember();
}
