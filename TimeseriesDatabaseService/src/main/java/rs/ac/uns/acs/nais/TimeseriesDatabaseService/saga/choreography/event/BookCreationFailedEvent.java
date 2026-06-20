package rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event;

import java.time.LocalDateTime;

public class BookCreationFailedEvent {
    private String sagaId;
    private String narudzbinaid;
    private String razlog;
    private LocalDateTime timestamp;

    public BookCreationFailedEvent() {
    }

    public BookCreationFailedEvent(String sagaId, String narudzbinaid, String razlog, LocalDateTime timestamp) {
        this.sagaId = sagaId;
        this.narudzbinaid = narudzbinaid;
        this.razlog = razlog;
        this.timestamp = timestamp;
    }

    public String getSagaId() { return sagaId; }
    public void setSagaId(String sagaId) { this.sagaId = sagaId; }
    public String getNarudzbinaid() { return narudzbinaid; }
    public void setNarudzbinaid(String narudzbinaid) { this.narudzbinaid = narudzbinaid; }
    public String getRazlog() { return razlog; }
    public void setRazlog(String razlog) { this.razlog = razlog; }
    public LocalDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(LocalDateTime timestamp) { this.timestamp = timestamp; }
}