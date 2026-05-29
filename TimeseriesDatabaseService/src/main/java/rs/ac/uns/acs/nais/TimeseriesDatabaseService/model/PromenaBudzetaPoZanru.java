package rs.ac.uns.acs.nais.TimeseriesDatabaseService.model;

import com.influxdb.annotations.Column;
import com.influxdb.annotations.Measurement;

import java.time.Instant;

/**
 * InfluxDB measurement za praćenje promena budžeta po žanru.
 *
 * Svaka nabavka, povraćaj ili korekcija budžeta upisuje se kao novi zapis.
 *
 * Tagovi:
 *   zanr      — FIKCIJA / LJUBVANI ROMANI / TRILER itd
 *   tipPromene — NABAVKA / POVRACAJ / KOREKCIJA_BUDZETA
 *
 * Fields:
 *   promenaStanja     — negativno = trošak (NABAVKA), pozitivno = povraćaj/korekcija
 *   raspolozivoStanje — stanje budžeta za ovaj žanr NAKON ove promene
 *   ukupniBudzet      — ukupno odobreni godišnji budžet za žanr
 *   napomena          — opciono
 */
@Measurement(name = "PromenaBudzetaPoZanru")
public class PromenaBudzetaPoZanru {

    @Column(tag = true)
    private String zanr;

    @Column(tag = true)
    private String tipPromene;

    @Column
    private Double promenaStanja;

    @Column
    private Double raspolozivoStanje;

    @Column
    private Double ukupniBudzet;

    @Column
    private String napomena;

    @Column(timestamp = true)
    private Instant timestamp;

    public PromenaBudzetaPoZanru() {}

    public String getZanr() { return zanr; }
    public void setZanr(String zanr) { this.zanr = zanr; }

    public String getTipPromene() { return tipPromene; }
    public void setTipPromene(String tipPromene) { this.tipPromene = tipPromene; }

    public Double getPromenaStanja() { return promenaStanja; }
    public void setPromenaStanja(Double promenaStanja) { this.promenaStanja = promenaStanja; }

    public Double getRaspolozivoStanje() { return raspolozivoStanje; }
    public void setRaspolozivoStanje(Double raspolozivoStanje) { this.raspolozivoStanje = raspolozivoStanje; }

    public Double getUkupniBudzet() { return ukupniBudzet; }
    public void setUkupniBudzet(Double ukupniBudzet) { this.ukupniBudzet = ukupniBudzet; }

    public String getNapomena() { return napomena; }
    public void setNapomena(String napomena) { this.napomena = napomena; }

    public Instant getTimestamp() { return timestamp; }
    public void setTimestamp(Instant timestamp) { this.timestamp = timestamp; }
}
