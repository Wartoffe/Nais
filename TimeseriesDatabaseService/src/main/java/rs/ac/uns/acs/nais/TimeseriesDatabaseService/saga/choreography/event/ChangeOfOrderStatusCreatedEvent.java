package rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event;

import rs.ac.uns.acs.nais.TimeseriesDatabaseService.dto.KnjigaDTO;

import java.time.LocalDateTime;
import java.util.List;

public class ChangeOfOrderStatusCreatedEvent {
    private String sagaId;
    private String narudzbinaid;
    private List<KnjigaDTO> knjige;
    private LocalDateTime timestamp;

    public ChangeOfOrderStatusCreatedEvent() {
    }

    public ChangeOfOrderStatusCreatedEvent(String sagaId, String narudzbinaid, List<KnjigaDTO> knjige, LocalDateTime timestamp) {
        this.sagaId = sagaId;
        this.narudzbinaid = narudzbinaid;
        this.knjige = knjige;
        this.timestamp = timestamp;
    }

    public String getNarudzbinaid() {
        return narudzbinaid;
    }

    public void setNarudzbinaid(String narudzbinaid) {
        this.narudzbinaid = narudzbinaid;
    }

    public String getSagaId() {
        return sagaId;
    }

    public void setSagaId(String sagaId) {
        this.sagaId = sagaId;
    }

    public List<KnjigaDTO> getKnjige() {
        return knjige;
    }

    public void setKnjige(List<KnjigaDTO> knjige) {
        this.knjige = knjige;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }
}
