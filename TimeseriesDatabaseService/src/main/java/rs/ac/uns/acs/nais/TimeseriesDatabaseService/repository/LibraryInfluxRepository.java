package rs.ac.uns.acs.nais.TimeseriesDatabaseService.repository;

import com.influxdb.query.FluxRecord;
import org.springframework.stereotype.Repository;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaBudzetaPoZanru;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaPredlogaZaNabavku;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaStatusaPorudzbine;

import java.util.List;

@Repository
public interface LibraryInfluxRepository {

    // ── PromenaStatusaPorudzbine ──────────────────────────────────
    Boolean saveStatusPromena(PromenaStatusaPorudzbine m);
    List<PromenaStatusaPorudzbine> findStatusByNarudzbinaid(String narudzbinaid);
    List<PromenaStatusaPorudzbine> findStatusByNoviStatus(String noviStatus, int days);


    // ── PromenaBudzetaPoZanru ─────────────────────────────────────
    Boolean saveBudzetPromena(PromenaBudzetaPoZanru m);
    List<PromenaBudzetaPoZanru> findBudzetByZanr(String zanr);
    List<PromenaBudzetaPoZanru> findBudzetByTipPromene(String tipPromene);


    // ── PromenaPredlogaZaNabavku ──────────────────────────────────
    Boolean savePredlogPromena(PromenaPredlogaZaNabavku m);
    List<PromenaPredlogaZaNabavku> findPredlogByPredlogid(String predlogid);
    List<PromenaPredlogaZaNabavku> findPredlogByZanr(String zanr);


    // ── Složeni upiti ─────────────────────────────────────────────
    List<FluxRecord> avgVremeIsporukePoDobavclja(int days);
    List<FluxRecord> budzetPoZanruMesecno(int months);
    List<FluxRecord> odobreniPredloziPoZanru(int days);
    List<FluxRecord> otkazivanjePoDobavclja(int days);
}
