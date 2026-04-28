package rs.ac.uns.acs.nais.GraphDatabaseService.model;

import org.springframework.data.neo4j.core.schema.*;
import java.util.List;

@Node
public class Knjiga {

    @Id
    private String isbn;
    private String naziv;
    private String autor;
    private Integer godinaIzdavanja;
    private Double cena;

    @Relationship(type = "PRIPADA", direction = Relationship.Direction.OUTGOING)
    private Zanr zanr;

    @Relationship(type = "JE_TREND", direction = Relationship.Direction.OUTGOING)
    private List<KnjigaTrendRelacija> trendovi;

    public Knjiga() {}

    public String getIsbn() { return isbn; }
    public void setIsbn(String isbn) { this.isbn = isbn; }

    public String getNaziv() { return naziv; }
    public void setNaziv(String naziv) { this.naziv = naziv; }

    public String getAutor() { return autor; }
    public void setAutor(String autor) { this.autor = autor; }

    public Integer getGodinaIzdavanja() { return godinaIzdavanja; }
    public void setGodinaIzdavanja(Integer godinaIzdavanja) { this.godinaIzdavanja = godinaIzdavanja; }

    public Double getCena() { return cena; }
    public void setCena(Double cena) { this.cena = cena; }

    public Zanr getZanr() { return zanr; }
    public void setZanr(Zanr zanr) { this.zanr = zanr; }

    public List<KnjigaTrendRelacija> getTrendovi() { return trendovi; }
    public void setTrendovi(List<KnjigaTrendRelacija> trendovi) { this.trendovi = trendovi; }
}
