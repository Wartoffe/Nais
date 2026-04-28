package rs.ac.uns.acs.nais.GraphDatabaseService.model;

import org.springframework.data.neo4j.core.schema.*;

@Node
public class Zanr {

    @Id
    private String naziv;

    private String opis;

    public Zanr() {}

    public String getNaziv() { return naziv; }
    public void setNaziv(String naziv) { this.naziv = naziv; }

    public String getOpis() { return opis; }
    public void setOpis(String opis) { this.opis = opis; }
}
