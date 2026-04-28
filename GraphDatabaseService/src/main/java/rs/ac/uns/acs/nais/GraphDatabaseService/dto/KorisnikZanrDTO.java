package rs.ac.uns.acs.nais.GraphDatabaseService.dto;

public class KorisnikZanrDTO {
    private String zanr;
    private String ime;
    private String prezime;
    private String email;
    private Long ukupnoZahteva;

    public String getZanr() { return zanr; }
    public void setZanr(String zanr) { this.zanr = zanr; }

    public String getIme() { return ime; }
    public void setIme(String ime) { this.ime = ime; }

    public String getPrezime() { return prezime; }
    public void setPrezime(String prezime) { this.prezime = prezime; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public Long getUkupnoZahteva() { return ukupnoZahteva; }
    public void setUkupnoZahteva(Long u) { this.ukupnoZahteva = u; }
}