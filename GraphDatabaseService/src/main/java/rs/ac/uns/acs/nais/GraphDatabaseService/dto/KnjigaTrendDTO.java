package rs.ac.uns.acs.nais.GraphDatabaseService.dto;

public class KnjigaTrendDTO {
    private String nazivKnjige;
    private String isbn;
    private Double score;

    public KnjigaTrendDTO(String nazivKnjige, String isbn, Double score) {
        this.nazivKnjige = nazivKnjige;
        this.isbn = isbn;
        this.score = score;
    }

    public void setNazivKnjige(String naziv){
        this.nazivKnjige = naziv;
    }
    public String getNazivKnjige() {
        return nazivKnjige;
    }

    public void setScore(Double score){
        this.score = score;
    }
    public Double getScore() {
        return score;
    }

    public void setIsbn(String isbn) {
        this.isbn = isbn;
    }

    public String getIsbn() {
        return isbn;
    }
}
