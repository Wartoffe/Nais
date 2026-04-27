package rs.ac.uns.acs.nais.GraphDatabaseService.service;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Trend;
import rs.ac.uns.acs.nais.GraphDatabaseService.repository.TrendRepository;

import java.util.List;

@Service
public class TrendService {

    private final TrendRepository trendRepository;

    public TrendService(TrendRepository trendRepository) {
        this.trendRepository = trendRepository;
    }

    public List<Trend> findAll() {
        return trendRepository.findAll();
    }

    public Trend findById(String naziv) {
        return trendRepository.findById(naziv)
                .orElseThrow(() -> new RuntimeException("Trend nije pronadjen: " + naziv));
    }

    public Trend create(Trend trend) {
        return trendRepository.save(trend);
    }

    public Trend azuriraj(String naziv, Integer score, String period) {
        return trendRepository.azurirajTrend(naziv, score, period);
    }

    public void delete(String naziv) {
        trendRepository.obrisiTrend(naziv);
    }
}
