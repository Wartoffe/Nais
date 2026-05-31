package rs.ac.uns.acs.nais.TimeseriesDatabaseService.service;

import com.influxdb.query.FluxRecord;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaBudzetaPoZanru;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaPredlogaZaNabavku;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaStatusaPorudzbine;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.repository.LibraryInfluxRepositoryImpl;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Servis za sve InfluxDB operacije bibliotečkog sistema.
 * Delegira sve na LibraryInfluxRepositoryImpl
 */
@Service
public class LibraryInfluxService {

    private final LibraryInfluxRepositoryImpl repository;

    public LibraryInfluxService(LibraryInfluxRepositoryImpl repository) {
        this.repository = repository;
    }

    // === PromenaStatusaPorudzbine ===============================

    public boolean saveStatusPromena(PromenaStatusaPorudzbine m) {
        return repository.saveStatusPromena(m);
    }

    public List<PromenaStatusaPorudzbine> findStatusByNarudzbinaid(String narudzbinaid) {
        return repository.findStatusByNarudzbinaid(narudzbinaid);
    }

    public List<PromenaStatusaPorudzbine> findStatusByNoviStatus(String noviStatus, int days) {
        return repository.findStatusByNoviStatus(noviStatus, days);
    }

    // ====== PromenaBudzetaPoZanru ===============================

    public boolean saveBudzetPromena(PromenaBudzetaPoZanru m) {
        return repository.saveBudzetPromena(m);
    }

    public List<PromenaBudzetaPoZanru> findBudzetByZanr(String zanr) {
        return repository.findBudzetByZanr(zanr);
    }

    public List<PromenaBudzetaPoZanru> findBudzetByTipPromene(String tipPromene) {
        return repository.findBudzetByTipPromene(tipPromene);
    }


    // ============ PromenaPredlogaZaNabavku ===============================

    public boolean savePredlogPromena(PromenaPredlogaZaNabavku m) {
        return repository.savePredlogPromena(m);
    }

    public List<PromenaPredlogaZaNabavku> findPredlogByPredlogid(String predlogid) {
        return repository.findPredlogByPredlogid(predlogid);
    }

    public List<PromenaPredlogaZaNabavku> findPredlogByZanr(String zanr) {
        return repository.findPredlogByZanr(zanr);
    }


    // ========= Složeni upiti ===============================

    @Cacheable(value = "avgIsporuka", key = "#days")
    public List<Map<String, Object>> avgVremeIsporukePoDobavclja(int days) {
        return toSerializableRows(repository.avgVremeIsporukePoDobavclja(days));
    }

    @Cacheable(value = "budzetMesecno", key = "#months")
    public List<Map<String, Object>> budzetPoZanruMesecno(int months) {
        return toSerializableRows(repository.budzetPoZanruMesecno(months));
    }

    @Cacheable(value = "odobreniPredloziPoZanru", key = "#days")
    public List<Map<String, Object>> odobreniPredloziPoZanru(int days) {
        return toSerializableRows(repository.odobreniPredloziPoZanru(days));
    }

    @Cacheable(value = "otkazivanja", key = "#days")
    public List<Map<String, Object>> otkazivanjePoDobavclja(int days) {
        return toSerializableRows(repository.otkazivanjePoDobavclja(days));
    }

    private List<Map<String, Object>> toSerializableRows(List<FluxRecord> records) {
        List<Map<String, Object>> rows = new ArrayList<>();
        for (FluxRecord record : records) {
            Map<String, Object> row = new LinkedHashMap<>();
            record.getValues().forEach((key, value) -> row.put(key, normalizeValue(value)));
            rows.add(row);
        }
        return rows;
    }

    private Object normalizeValue(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number || value instanceof Boolean || value instanceof String) {
            return value;
        }
        return value.toString();
    }
}
