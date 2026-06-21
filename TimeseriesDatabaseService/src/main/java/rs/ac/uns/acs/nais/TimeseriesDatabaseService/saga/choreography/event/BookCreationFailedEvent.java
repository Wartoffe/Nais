package rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event;

import java.time.LocalDateTime;

public class BookCreationFailedEvent {
    private String sagaId;
    private String narudzbinaid;
    /*
     * Status koji je bio aktivan PRE koraka 1 (pre upisa PromenaStatusaPorudzbine koji je pokrenuo ovu SAGA instancu).
     * VectorDatabaseService ovu vrednost samo prosleđuje dalje iz primljenog ChangeOfOrderStatusCreatedEvent-a.
     * Sluzi CompensationListener-u da zna tacno na koji status da vrati narudzbinu.
     */
    private String prethodniStatus;
    private String razlog;
    private LocalDateTime timestamp;

    public BookCreationFailedEvent() {
    }

    public BookCreationFailedEvent(String sagaId, String narudzbinaid, String prethodniStatus, String razlog, LocalDateTime timestamp) {
        this.sagaId = sagaId;
        this.narudzbinaid = narudzbinaid;
        this.prethodniStatus = prethodniStatus;
        this.razlog = razlog;
        this.timestamp = timestamp;
    }

    public String getSagaId() { return sagaId; }
    public void setSagaId(String sagaId) { this.sagaId = sagaId; }

    public String getPrethodniStatus() {
        return prethodniStatus;
    }

    public void setPrethodniStatus(String prethodniStatus) {
        this.prethodniStatus = prethodniStatus;
    }
    public String getNarudzbinaid() { return narudzbinaid; }
    public void setNarudzbinaid(String narudzbinaid) { this.narudzbinaid = narudzbinaid; }
    public String getRazlog() { return razlog; }
    public void setRazlog(String razlog) { this.razlog = razlog; }
    public LocalDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(LocalDateTime timestamp) { this.timestamp = timestamp; }
}