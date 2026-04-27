package rs.ac.uns.acs.nais.GraphDatabaseService.model;

import org.springframework.data.neo4j.core.schema.*;

@Node
public class Trend {

    @Id
    private String naziv; // naziv je prirodni ID (npr. "BookTok")

    private String period;  // npr. "2024-Q1"
    private Integer score;  // 0-100

    public Trend() {}

    public String getNaziv() { return naziv; }
    public void setNaziv(String naziv) { this.naziv = naziv; }

    public String getPeriod() { return period; }
    public void setPeriod(String period) { this.period = period; }

    public Integer getScore() { return score; }
    public void setScore(Integer score) { this.score = score; }
}
