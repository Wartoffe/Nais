package rs.ac.uns.acs.nais.GraphDatabaseService.model;

import org.springframework.data.neo4j.core.schema.*;

@Node
public class Trend {

    @Id
    private String naziv;
    private String period;
    private Integer score;
    public Trend() {}

    public String getNaziv() { return naziv; }
    public void setNaziv(String naziv) { this.naziv = naziv; }

    public String getPeriod() { return period; }
    public void setPeriod(String period) { this.period = period; }

    public Integer getScore() { return score; }
    public void setScore(Integer score) { this.score = score; }
}
