package rs.ac.uns.acs.nais.TimeseriesDatabaseService.model;

import com.influxdb.annotations.Column;
import com.influxdb.annotations.Measurement;

import java.time.Instant;

/**
 * InfluxDB measurement za praćenje promena statusa predloga za nabavku.
 *
 * Svaka promena statusa predloga upisuje se kao novi zapis.
 * Predlog uvek počinje sa status=NA_CEKANJU (minuteUCekanju=0),
 * a zatim dobija ODOBREN ili ODBIJEN.
 *
 * Tagovi:
 *   predlogid   — ID predloga iz relacione BP
 *   zanr        — žanr knjige koja se predlaže za nabavku
 *   status      — NA_CEKANJU / ODOBREN / ODBIJEN
 *
 * Fieldi:
 *   minuteUCekanju — koliko minuta je predlog bio u prethodnom statusu (0 za NA_CEKANJU)
 *   procenjenaCena — procenjena cena nabavke u RSD
 *   naslovKnjige   — opciono, radi čitljivosti rezultata
 */
@Measurement(name = "PromenaPredlogaZaNabavku")
public class PromenaPredlogaZaNabavku {

    @Column(tag = true)
    private String predlogid;

    @Column(tag = true)
    private String zanr;

    @Column(tag = true)
    private String status;

    @Column
    private Long minuteUCekanju;

    @Column
    private Double procenjenaCena;

    @Column
    private String naslovKnjige;

    @Column(timestamp = true)
    private Instant timestamp;

    public PromenaPredlogaZaNabavku() {}

    public String getPredlogid() { return predlogid; }
    public void setPredlogid(String predlogid) { this.predlogid = predlogid; }

    public String getZanr() { return zanr; }
    public void setZanr(String zanr) { this.zanr = zanr; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public Long getMinuteUCekanju() { return minuteUCekanju; }
    public void setMinuteUCekanju(Long minuteUCekanju) { this.minuteUCekanju = minuteUCekanju; }

    public Double getProcenjenaCena() { return procenjenaCena; }
    public void setProcenjenaCena(Double procenjenaCena) { this.procenjenaCena = procenjenaCena; }

    public String getNaslovKnjige() { return naslovKnjige; }
    public void setNaslovKnjige(String naslovKnjige) { this.naslovKnjige = naslovKnjige; }

    public Instant getTimestamp() { return timestamp; }
    public void setTimestamp(Instant timestamp) { this.timestamp = timestamp; }
}
