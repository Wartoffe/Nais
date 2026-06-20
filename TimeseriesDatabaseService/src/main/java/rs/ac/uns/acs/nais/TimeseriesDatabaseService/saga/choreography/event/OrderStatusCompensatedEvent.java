package rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event;

import java.time.LocalDateTime;

/*
 * Objavljuje se nakon sto CompensationListener uspesno vrati prethodno aktivni
 * status porudzbine. Sluzi za audit trag i eventualnu notifikaciju drugih
 * zainteresovanih servisa da je SAGA zavrsena kompenzacijom (a ne uspehom).
 */
public class OrderStatusCompensatedEvent {
    private String sagaId;
    private String narudzbinaid;
    private String vracenNaStatus;
    private LocalDateTime timestamp;

    public OrderStatusCompensatedEvent() {
    }

    public OrderStatusCompensatedEvent(String sagaId, String narudzbinaid, String vracenNaStatus, LocalDateTime timestamp) {
        this.sagaId = sagaId;
        this.narudzbinaid = narudzbinaid;
        this.vracenNaStatus = vracenNaStatus;
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

    public String getVracenNaStatus() {
        return vracenNaStatus;
    }

    public void setVracenNaStatus(String vracenNaStatus) {
        this.vracenNaStatus = vracenNaStatus;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }
}