package rs.ac.uns.acs.nais.GraphDatabaseService.dto;

public class TopKnjigaDTO {
    private String isbn;
    private String naziv;
    private String autor;
    private Long ukupnoZahteva;

    public TopKnjigaDTO(String isbn, String naziv, String autor, Long ukupnoZahteva) {
        this.isbn = isbn;
        this.naziv = naziv;
        this.autor = autor;
        this.ukupnoZahteva = ukupnoZahteva;
    }

    public void setNaziv(String naziv) {
        this.naziv = naziv;
    }

    public String getNaziv() {
        return naziv;
    }

    public void setIsbn(String isbn) {
        this.isbn = isbn;
    }

    public String getIsbn() {
        return isbn;
    }

    public void setAutor(String autor){
        this.autor=autor;
    }

    public String getAutor() {
        return autor;
    }

    public void setUkupnoZahteva(Long ukupnoZahteva) {
        this.ukupnoZahteva = ukupnoZahteva;
    }

    public Long getUkupnoZahteva() {
        return  ukupnoZahteva;
    }

}
