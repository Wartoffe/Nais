package rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event;

import rs.ac.uns.acs.nais.TimeseriesDatabaseService.dto.KnjigaDTO;

import java.time.LocalDateTime;
import java.util.List;

public class ChangeOfOrderStatusCreatedEvent {
    private String sagaId;
    private String narudzbinaid;
    /*
     * Status koji je bio aktivan PRE ovog upisa (pre koraka 1). Prenosi se kroz ceo
     * lanac eventa kako bi, u slucaju neuspeha u VectorDatabaseService, kompenzacija
     * znala tacno na koji status da vrati narudzbinu - bez upita nad InfluxDB.
     */
    private String prethodniStatus;
    private List<KnjigaDTO> knjige;
    private LocalDateTime timestamp;

    public ChangeOfOrderStatusCreatedEvent() {
    }

    public ChangeOfOrderStatusCreatedEvent(String sagaId, String narudzbinaid, String prethodniStatus, List<KnjigaDTO> knjige, LocalDateTime timestamp) {
        this.sagaId = sagaId;
        this.narudzbinaid = narudzbinaid;
        this.prethodniStatus = prethodniStatus;
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

    public String getPrethodniStatus() {
        return prethodniStatus;
    }

    public void setPrethodniStatus(String prethodniStatus) {
        this.prethodniStatus = prethodniStatus;
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
