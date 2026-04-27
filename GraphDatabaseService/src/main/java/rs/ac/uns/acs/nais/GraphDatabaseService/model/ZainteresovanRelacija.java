package rs.ac.uns.acs.nais.GraphDatabaseService.model;

import org.springframework.data.neo4j.core.schema.*;
import java.time.LocalDate;

@RelationshipProperties
public class ZainteresovanRelacija {

    @RelationshipId
    private Long id;

    private LocalDate datumZahteva;
    private Integer brojZahteva;

    @TargetNode
    private Knjiga knjiga;

    public ZainteresovanRelacija() {}

    public Long getId() { return id; }

    public LocalDate getDatumZahteva() { return datumZahteva; }
    public void setDatumZahteva(LocalDate datumZahteva) { this.datumZahteva = datumZahteva; }

    public Integer getBrojZahteva() { return brojZahteva; }
    public void setBrojZahteva(Integer brojZahteva) { this.brojZahteva = brojZahteva; }

    public Knjiga getKnjiga() { return knjiga; }
    public void setKnjiga(Knjiga knjiga) { this.knjiga = knjiga; }
}
