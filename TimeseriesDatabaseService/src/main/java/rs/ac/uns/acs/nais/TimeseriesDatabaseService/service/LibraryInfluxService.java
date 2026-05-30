package rs.ac.uns.acs.nais.TimeseriesDatabaseService.service;

import com.influxdb.query.FluxRecord;
import org.springframework.stereotype.Service;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaBudzetaPoZanru;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaPredlogaZaNabavku;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaStatusaPorudzbine;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.repository.LibraryInfluxRepositoryImpl;

import java.util.List;

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

    public List<FluxRecord> avgVremeIsporukePoDobavclja(int days) {
        return repository.avgVremeIsporukePoDobavclja(days);
    }

    public List<FluxRecord> budzetPoZanruMesecno(int months) {
        return repository.budzetPoZanruMesecno(months);
    }

    public List<FluxRecord> odobreniPredloziPoZanru(int days) {
        return repository.odobreniPredloziPoZanru(days);
    }

    public List<FluxRecord> otkazivanjePoDobavclja(int days) {
        return repository.otkazivanjePoDobavclja(days);
    }
}
