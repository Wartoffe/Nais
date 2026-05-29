package rs.ac.uns.acs.nais.TimeseriesDatabaseService.repository;

import com.influxdb.client.InfluxDBClient;
import com.influxdb.query.FluxRecord;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Repository;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.configuration.InfluxDBConnectionClass;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaBudzetaPoZanru;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaPredlogaZaNabavku;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaStatusaPorudzbine;

import java.util.List;

/**
 * Implementacija repository-ja — prati isti obrazac kao PurchaseRepositoryImpl:
 *   1. buildConnection()  — otvori klijenta
 *   2. pozovi operaciju   — na LibraryInfluxDBConnectionClass
 *   3. client.close()     — zatvori klijenta
 */
@Repository
public class LibraryInfluxRepositoryImpl implements LibraryInfluxRepository {

    @Autowired
    private final InfluxDBConnectionClass conn;

    public LibraryInfluxRepositoryImpl(InfluxDBConnectionClass conn) {
        this.conn = conn;
    }

    // ================================================================
    // PromenaStatusaPorudzbine
    // ================================================================

    @Override
    public Boolean saveStatusPromena(PromenaStatusaPorudzbine m) {
        InfluxDBClient client = conn.buildConnection();
        Boolean result = conn.saveStatusPromena(client, m);
        client.close();
        return result;
    }

    @Override
    public List<PromenaStatusaPorudzbine> findStatusByNarudzbinaid(String narudzbinaid) {
        InfluxDBClient client = conn.buildConnection();
        List<PromenaStatusaPorudzbine> result = conn.findAllByNarudzbinaid(client, narudzbinaid);
        client.close();
        return result;
    }

    @Override
    public List<PromenaStatusaPorudzbine> findStatusByNoviStatus(String noviStatus, int days) {
        InfluxDBClient client = conn.buildConnection();
        List<PromenaStatusaPorudzbine> result = conn.findAllByNoviStatus(client, noviStatus, days);
        client.close();
        return result;
    }


    // ================================================================
    // PromenaBudzetaPoZanru
    // ================================================================

    @Override
    public Boolean saveBudzetPromena(PromenaBudzetaPoZanru m) {
        InfluxDBClient client = conn.buildConnection();
        Boolean result = conn.saveBudzetPromena(client, m);
        client.close();
        return result;
    }

    @Override
    public List<PromenaBudzetaPoZanru> findBudzetByZanr(String zanr) {
        InfluxDBClient client = conn.buildConnection();
        List<PromenaBudzetaPoZanru> result = conn.findBudzetByZanr(client, zanr);
        client.close();
        return result;
    }

    @Override
    public List<PromenaBudzetaPoZanru> findBudzetByTipPromene(String tipPromene) {
        InfluxDBClient client = conn.buildConnection();
        List<PromenaBudzetaPoZanru> result = conn.findBudzetByTipPromene(client, tipPromene);
        client.close();
        return result;
    }


    // ================================================================
    // PromenaPredlogaZaNabavku
    // ================================================================

    @Override
    public Boolean savePredlogPromena(PromenaPredlogaZaNabavku m) {
        InfluxDBClient client = conn.buildConnection();
        Boolean result = conn.savePredlogPromena(client, m);
        client.close();
        return result;
    }

    @Override
    public List<PromenaPredlogaZaNabavku> findPredlogByPredlogid(String predlogid) {
        InfluxDBClient client = conn.buildConnection();
        List<PromenaPredlogaZaNabavku> result = conn.findPredlogByPredlogid(client, predlogid);
        client.close();
        return result;
    }

    @Override
    public List<PromenaPredlogaZaNabavku> findPredlogByZanr(String zanr) {
        InfluxDBClient client = conn.buildConnection();
        List<PromenaPredlogaZaNabavku> result = conn.findPredlogByZanr(client, zanr);
        client.close();
        return result;
    }


    // ================================================================
    // Složeni upiti
    // ================================================================

    @Override
    public List<FluxRecord> avgVremeIsporukePoDobavclja(int days) {
        InfluxDBClient client = conn.buildConnection();
        List<FluxRecord> result = conn.avgVremeIsporukePoDobavclja(client, days);
        client.close();
        return result;
    }

    @Override
    public List<FluxRecord> budzetPoZanruMesecno(int months) {
        InfluxDBClient client = conn.buildConnection();
        List<FluxRecord> result = conn.budzetPoZanruMesecno(client, months);
        client.close();
        return result;
    }

    @Override
    public List<FluxRecord> odobreniPredloziPoZanru(int days) {
        InfluxDBClient client = conn.buildConnection();
        List<FluxRecord> result = conn.odobreniPredloziPoZanru(client, days);
        client.close();
        return result;
    }

    @Override
    public List<FluxRecord> otkazivanjePoDobavclja(int days) {
        InfluxDBClient client = conn.buildConnection();
        List<FluxRecord> result = conn.otkazivanjePoDobavclja(client, days);
        client.close();
        return result;
    }
}
