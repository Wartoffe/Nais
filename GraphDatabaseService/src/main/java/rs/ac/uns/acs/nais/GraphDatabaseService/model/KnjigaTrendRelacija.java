package rs.ac.uns.acs.nais.GraphDatabaseService.model;

import org.springframework.data.neo4j.core.schema.*;

@RelationshipProperties
public class KnjigaTrendRelacija {

    @RelationshipId
    private Long id;

    private Double relevantnostScore; // 0.0 - 100.0

    @TargetNode
    private Trend trend;

    public KnjigaTrendRelacija() {}

    public Long getId() { return id; }

    public Double getRelevantnostScore() { return relevantnostScore; }
    public void setRelevantnostScore(Double relevantnostScore) { this.relevantnostScore = relevantnostScore; }

    public Trend getTrend() { return trend; }
    public void setTrend(Trend trend) { this.trend = trend; }
}
