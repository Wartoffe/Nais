package rs.ac.uns.acs.nais.GraphDatabaseService.dto;

public class TrendDTO {
    private String naziv;
    private String period;
    private Double score;

    public TrendDTO(String naziv, String period, Double score) {
        this.naziv = naziv;
        this.period = period;
        this.score = score;
    }

    public void setNaziv(String naziv){
        this.naziv = naziv;
    }
    public String getNaziv() {
        return naziv;
    }

    public void setPeriod(String period){
        this.period = period;
    }
    public String getPeriod() {
        return period;
    }

    public void setScore(Double score){
        this.score = score;
    }
    public Double getScore() {
        return score;
    }
}
