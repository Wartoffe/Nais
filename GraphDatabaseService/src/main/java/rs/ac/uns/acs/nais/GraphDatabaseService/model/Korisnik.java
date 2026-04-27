package rs.ac.uns.acs.nais.GraphDatabaseService.model;

import org.springframework.data.neo4j.core.schema.*;
import java.util.List;

@Node
public class Korisnik {

    @Id
    private String email; // email je prirodni ID

    private String ime;
    private String prezime;
    private String tipKorisnika; // "student", "nastavnik", "clan"

    @Relationship(type = "ZAINTERESOVAN_ZA", direction = Relationship.Direction.OUTGOING)
    private List<ZainteresovanRelacija> zahtevaneKnjige;

    public Korisnik() {}

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getIme() { return ime; }
    public void setIme(String ime) { this.ime = ime; }

    public String getPrezime() { return prezime; }
    public void setPrezime(String prezime) { this.prezime = prezime; }

    public String getTipKorisnika() { return tipKorisnika; }
    public void setTipKorisnika(String tipKorisnika) { this.tipKorisnika = tipKorisnika; }

    public List<ZainteresovanRelacija> getZahtevaneKnjige() { return zahtevaneKnjige; }
    public void setZahtevaneKnjige(List<ZainteresovanRelacija> zahtevaneKnjige) { this.zahtevaneKnjige = zahtevaneKnjige; }
}
