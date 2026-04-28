package rs.ac.uns.acs.nais.GraphDatabaseService.dto;

public class ZahtevDTO {
    private String naziv;
    private String isbn;
    private Long brojZahteva;

    public ZahtevDTO(String naziv, String isbn, Long brojZahteva) {
        this.naziv = naziv;
        this.isbn = isbn;
        this.brojZahteva = brojZahteva;
    }

    public String getNaziv() {
        return naziv;
    }

    public void setNaziv(String naziv) {
        this.naziv = naziv;
    }

    public void setIsbn(String isbn){
        this.isbn= isbn;
    }

    public String getIsbn(){
        return isbn;
    }

    public void setBrojZahteva(Long brojZahteva){
        this.brojZahteva = brojZahteva;
    }
}