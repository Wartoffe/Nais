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
            MATCH (m:Member {id: $memberId})
            MATCH (b:Book) WHERE b.id IN m.bookHistory
            MATCH (b)-[:BELONGS_TO]->(g:Genre)<-[:BELONGS_TO]-(rec:Book)
            WHERE NOT rec.id IN m.bookHistory
            WITH rec, COUNT(g) AS score
            RETURN rec
            ORDER BY score DESC
            """)
    List<Book> recommendByGenre(Long memberId);

    //2
    @Query("""
            MATCH (m:Member {id: $memberId})
            MATCH (b:Book) WHERE b.id IN m.bookHistory
            MATCH (b)-[s:SIMILAR_TO]->(rec:Book)
            WHERE NOT rec.id IN m.bookHistory
            WITH rec, COUNT(s) AS similarityScore
            RETURN rec
            ORDER BY similarityScore DESC
            """)
    List<Book> recommendBySimilarity(Long memberId);
    @Query("""
            MATCH (m:Member {id: $memberId})
            MATCH (b:Book) WHERE b.id IN m.bookHistory
            MATCH (b)-[:WRITTEN_BY]->(a:Author)<-[:WRITTEN_BY]-(rec:Book)
            WHERE NOT rec.id IN m.bookHistory
            RETURN rec
            """)
    List<Book> recommendByAuthor(Long memberId);

    @Query("""
            MATCH (m:Member {id: $memberId})
            MATCH (b:Book) WHERE b.id IN m.bookHistory

            OPTIONAL MATCH (b)-[:BELONGS_TO]->(g:Genre)<-[:BELONGS_TO]-(rec1:Book)
            WHERE NOT rec1.id IN m.bookHistory
            WITH m, b, rec1, COUNT(g) AS genreScore

            OPTIONAL MATCH (b)-[s:SIMILAR_TO]->(rec2:Book)
            WHERE NOT rec2.id IN m.bookHistory
            WITH m, b, rec1, genreScore, rec2, COUNT(s) AS similarityScore

            OPTIONAL MATCH (b)-[:WRITTEN_BY]->(a:Author)<-[:WRITTEN_BY]-(rec3:Book)
            WHERE NOT rec3.id IN m.bookHistory
            WITH rec1, rec2, rec3, genreScore, similarityScore, COUNT(a) AS authorScore

            WITH coalesce(rec1, rec2, rec3) AS rec, genreScore, similarityScore, authorScore
            WHERE rec IS NOT NULL

            WITH rec, SUM(genreScore) AS genreScore, SUM(similarityScore) AS similarityScore, SUM(authorScore) AS authorScore
            RETURN rec, (genreScore * 2 + similarityScore * 3 + authorScore * 1) AS totalScore
            sORDER BY totalScore DESC
        """)
    List<Book> recommendCombined(Long memberId);


    @Query("""
            MATCH (b1:Book {id: $bookId})-[r1:SIMILAR_TO]->(b2:Book {id: $targetBookId})
            DELETE r1
            WITH b1, b2
            MATCH (b2)-[r2:SIMILAR_TO]->(b1)
            DELETE r2
            """)
    void deleteSimilarBothDirections(String bookId, String targetBookId);
}
