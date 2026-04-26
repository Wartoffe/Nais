package rs.ac.uns.acs.Repository;

import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.neo4j.repository.query.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import rs.ac.uns.acs.Model.Member;

import java.time.LocalDate;
import java.util.Date;

@Repository
public interface MemberRepository extends Neo4jRepository<Member, Long> {

    @Query("""
            MATCH (m:Member {id: $memberId})-[r:BORROWED]->(b:Book {id: $bookId})
            SET r.date = $date
            """)
    void updateBorrowDate(Long memberId, String bookId, LocalDate date);

    @Query("""
            MATCH (m:Member {id: $memberId})-[r:BORROWED]->(b:Book {id: $bookId})
            DELETE r
            """)
    void deleteBorrowRelationship(Long memberId, String bookId);
}
