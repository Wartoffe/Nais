package rs.ac.uns.acs.nais.TimeseriesDatabaseService.model;

import com.influxdb.annotations.Column;
import com.influxdb.annotations.Measurement;

import java.time.Instant;

/**
 * InfluxDB measurement za praćenje promene statusa narudžbine.
 *
 * Svaki put kada se status narudžbine promeni u relacionoj BP,
 * upisuje se NOVI zapis ovde — stari se ne menja (append-only).
 *
 * Tagovi (indeksirani, za filtriranje):
 *   narudzbinaid   — IdN iz relacione BP
 *   dobavljacid    — IdDob iz relacione BP
 *   dobavljacnaziv — NazivDob (denormalizovano radi čitljivosti upita)
 *   prethodniStatus — prethodni status (NONE ako je KREIRANA)
 *   noviStatus      — KREIRANA / POSLATA / ISPORUCENA / OTKAZANA
 *
 * Fieldi (numeričke vrednosti za agregacije):
 *   minuteUCekanju     — koliko minuta je narudžbina bila u prethodnom statusu
 *   vrednostNarudzbine — VrednostN iz relacione BP
 *   brojStavki         — broj stavki narudžbine (opciono)
 */
@Measurement(name = "PromenaStatusaPorudzbine")
public class PromenaStatusaPorudzbine {

    @Column(tag = true)
    private String narudzbinaid;

    @Column(tag = true)
    private String dobavljacid;

    @Column(tag = true)
    private String dobavljacnaziv;

    @Column(tag = true)
    private String prethodniStatus;

    @Column(tag = true)
    private String noviStatus;

    @Column
    private Long minuteUCekanju;

    @Column
    private Double vrednostNarudzbine;

    @Column
    private Integer brojStavki;

    @Column(timestamp = true)
    private Instant timestamp;

    public PromenaStatusaPorudzbine() {}

    public String getNarudzbinaid() { return narudzbinaid; }
    public void setNarudzbinaid(String narudzbinaid) { this.narudzbinaid = narudzbinaid; }

    public String getDobavljacid() { return dobavljacid; }
    public void setDobavljacid(String dobavljacid) { this.dobavljacid = dobavljacid; }

    public String getDobavljacnaziv() { return dobavljacnaziv; }
    public void setDobavljacnaziv(String dobavljacnaziv) { this.dobavljacnaziv = dobavljacnaziv; }

    public String getPrethodniStatus() { return prethodniStatus; }
    public void setPrethodniStatus(String prethodniStatus) { this.prethodniStatus = prethodniStatus; }

    public String getNoviStatus() { return noviStatus; }
    public void setNoviStatus(String noviStatus) { this.noviStatus = noviStatus; }

    public Long getMinuteUCekanju() { return minuteUCekanju; }
    public void setMinuteUCekanju(Long minuteUCekanju) { this.minuteUCekanju = minuteUCekanju; }

    public Double getVrednostNarudzbine() { return vrednostNarudzbine; }
    public void setVrednostNarudzbine(Double vrednostNarudzbine) { this.vrednostNarudzbine = vrednostNarudzbine; }

    public Integer getBrojStavki() { return brojStavki; }
    public void setBrojStavki(Integer brojStavki) { this.brojStavki = brojStavki; }

    public Instant getTimestamp() { return timestamp; }
    public void setTimestamp(Instant timestamp) { this.timestamp = timestamp; }
}
