package rs.ac.uns.acs.Repository;

import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.neo4j.repository.query.Query;
import org.springframework.stereotype.Repository;
import rs.ac.uns.acs.Model.Book;

import java.util.List;

@Repository
public interface BookRepository extends Neo4jRepository<Book, String> {

    @Query("MATCH (b:Book{id: $bookId}) MATCH (g:Genre{id:$genreId}) MERGE (b)-[:BELONGS_TO]->(g)")
    void addGenreToBook(String bookId, Long genreId);

    @Query("MATCH (b1:Book)-[:BELONGS_TO]->(g:Genre)<-[:BELONGS_TO]-(b2:Book) WHERE b1.id <> b2.id MERGE (b1)-[s:SIMILAR_TO]->(b2) ON CREATE SET s.score=1.0")
    void createSimilarityByGenre();

    //1.
    @Query("""
            MATCH (m:Member {id: $memberId})-[:BORROWED]-> (b:Book)
            MATCH (b)-[:BELONGS_TO]->(g:Genre)<- [:BELONGS_TO]-(rec:Book)
            WHERE NOT (m)-[:BORROWED]->(rec)
            WITH rec, COUNT(g) AS score
            WHERE score >0
            RETURN rec
            ORDER BY score DESC
            """)
    List<Book> recommendByGenre(Long memberId);

    //2
    @Query("""
            MATCH (m:Member {id: $memberId})-[:BORROWED]->(b:Book)
            MATCH (b)-[s:SIMILAR_TO]->(rec:Book)
            WHERE NOT (m)-[:BORROWED]->(rec)
            WITH rec, COUNT(s) AS similarityScore
            WHERE similarityScore > 0
            RETURN rec
            ORDER BY similarityScore DESC
            """)
    List<Book> recommendBySimilarity(Long memberId);

}
