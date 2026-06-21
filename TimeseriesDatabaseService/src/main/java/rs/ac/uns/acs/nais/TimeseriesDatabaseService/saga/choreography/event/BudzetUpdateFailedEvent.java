package rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event;

// Objavkjuje ga TimeseriesDatabaseService kada ne uspe da upise promenu budzeta u bazu podataka
// Slusa ga BookAndReviewsSearchService i i kao kompenzaciju vraca obrisanu knjigu (iz snapshot-a sačuvanog pre brisanja).

import java.time.LocalDateTime;

public class BudzetUpdateFailedEvent {
    private String sagaId;
    private String bookId;
    private String razlog;
    private LocalDateTime timestamp;

    public BudzetUpdateFailedEvent() {
    }

    public BudzetUpdateFailedEvent(String sagaId, String bookId, String razlog, LocalDateTime timestamp) {
        this.sagaId = sagaId;
        this.bookId = bookId;
        this.razlog = razlog;
        this.timestamp = timestamp;
    }

    public String getSagaId() { return sagaId; }
    public void setSagaId(String sagaId) { this.sagaId = sagaId; }
    public String getBookId() { return bookId; }
    public void setBookId(String bookId) { this.bookId = bookId; }
    public String getRazlog() { return razlog; }
    public void setRazlog(String razlog) { this.razlog = razlog; }
    public LocalDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(LocalDateTime timestamp) { this.timestamp = timestamp; }
}
