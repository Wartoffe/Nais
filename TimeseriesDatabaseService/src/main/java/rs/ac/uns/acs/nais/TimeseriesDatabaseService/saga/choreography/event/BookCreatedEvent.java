package rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event;

import java.time.LocalDateTime;

public class BookCreatedEvent {
    private String sagaId;
    private String narudzbinaid;
    private LocalDateTime timestamp;

    public BookCreatedEvent() {
    }

    public BookCreatedEvent(String sagaId, String narudzbinaid, LocalDateTime timestamp) {
        this.sagaId = sagaId;
        this.narudzbinaid = narudzbinaid;
        this.timestamp = timestamp;
    }

    public String getSagaId() {
        return sagaId;
    }

    public void setSagaId(String sagaId) {
        this.sagaId = sagaId;
    }

    public String getNarudzbinaid() {
        return narudzbinaid;
    }

    public void setNarudzbinaid(String narudzbinaid) {
        this.narudzbinaid = narudzbinaid;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }
}
