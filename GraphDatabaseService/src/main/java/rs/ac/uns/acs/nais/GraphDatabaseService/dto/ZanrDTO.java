package rs.ac.uns.acs.nais.GraphDatabaseService.dto;

public class ZanrDTO {
    private String naziv;
    private String opis;

    public ZanrDTO(String naziv, String opis) {
        this.naziv = naziv;
        this.opis = opis;
    }

    public void setNaziv(String naziv) {
        this.naziv = naziv;
    }

    public String getNaziv() {
        return naziv;
    }

    public void setOpis(String opis) {
        this.opis = opis;
    }

    public String getOpis() {
        return opis;
    }
}
