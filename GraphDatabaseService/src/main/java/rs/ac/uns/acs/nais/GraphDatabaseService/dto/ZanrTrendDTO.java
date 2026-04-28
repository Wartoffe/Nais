package rs.ac.uns.acs.nais.GraphDatabaseService.dto;

public class ZanrTrendDTO {
    private String zanr;
    private String trendIme;
    private Double prosecnaRelevantnost;
    private Long brojKnjiga;

    public String getZanr() { return zanr; }
    public void setZanr(String zanr) { this.zanr = zanr; }

    public String getTrendIme() { return trendIme; }
    public void setTrendIme(String trendIme) { this.trendIme = trendIme; }

    public Double getProsecnaRelevantnost() { return prosecnaRelevantnost; }
    public void setProsecnaRelevantnost(Double prosecnaRelevantnost) { this.prosecnaRelevantnost = prosecnaRelevantnost; }

    public Long getBrojKnjiga() { return brojKnjiga; }
    public void setBrojKnjiga(Long brojKnjiga) { this.brojKnjiga = brojKnjiga; }
}
