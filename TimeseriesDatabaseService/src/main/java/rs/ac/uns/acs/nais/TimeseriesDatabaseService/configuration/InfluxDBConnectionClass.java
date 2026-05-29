package rs.ac.uns.acs.nais.TimeseriesDatabaseService.configuration;

import java.time.Instant;

import java.util.ArrayList;
import java.util.List;

import com.influxdb.client.InfluxDBClient;
import com.influxdb.client.InfluxDBClientFactory;
import com.influxdb.client.QueryApi;
import com.influxdb.client.WriteApiBlocking;
import com.influxdb.client.domain.WritePrecision;
import com.influxdb.client.write.Point;
import com.influxdb.exceptions.InfluxException;
import com.influxdb.query.FluxRecord;
import com.influxdb.query.FluxTable;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaBudzetaPoZanru;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaPredlogaZaNabavku;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaStatusaPorudzbine;

@Component
public class InfluxDBConnectionClass {

    @Value("${spring.influx.token}")
    private String token;

    @Value("${spring.influx.bucket}")
    private String bucket;

    @Value("${spring.influx.org}")
    private String org;

    @Value("${spring.influx.url}")
    private String url;

    public InfluxDBClient buildConnection() {
        return InfluxDBClientFactory.create(url, token.toCharArray(), org, bucket);
    }
    public String getToken() { return token; }
    public void setToken(String token) { this.token = token; }
    public String getBucket() { return bucket; }
    public void setBucket(String bucket) { this.bucket = bucket; }

    public String getOrg() { return org; }
    public void setOrg(String org) { this.org = org; }
    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }

    // MERENJE 1 -> CREATE

    /**
     * Upisuje jedan event promene statusa narudžbine.
     * Ako timestamp nije setovan na modelu, koristi se Instant.now().
     */
    public boolean saveStatusPromena(InfluxDBClient client, PromenaStatusaPorudzbine m) {
        try {
            WriteApiBlocking writeApi = client.getWriteApiBlocking();
            if (m.getTimestamp() == null) m.setTimestamp(Instant.now());

            Point point = Point.measurement("PromenaStatusaPorudzbine")
                    .time(m.getTimestamp(), WritePrecision.MS)
                    .addTag("narudzbinaid",    m.getNarudzbinaid())
                    .addTag("dobavljacid",     m.getDobavljacid())
                    .addTag("dobavljacnaziv",  m.getDobavljacnaziv())
                    .addTag("prethodniStatus", m.getPrethodniStatus() != null ? m.getPrethodniStatus() : "NONE")
                    .addTag("noviStatus",      m.getNoviStatus())
                    .addField("minuteUCekanju",     m.getMinuteUCekanju())
                    .addField("vrednostNarudzbine", m.getVrednostNarudzbine());

            if (m.getBrojStavki() != null)
                point.addField("brojStavki", m.getBrojStavki());

            writeApi.writePoint(point);
            return true;
        } catch (InfluxException e) {
            return false;
        }
    }


    // MERENJE 1 ->  READ

    /** Vraća kompletan lifecycle jedne narudžbine, sortiran hronološki. */
    public List<PromenaStatusaPorudzbine> findAllByNarudzbinaid(InfluxDBClient client, String narudzbinaid) {
        String flux = String.format(
                "from(bucket:\"%s\") " +
                        "|> range(start: 0) " +
                        "|> filter(fn: (r) => r[\"_measurement\"] == \"PromenaStatusaPorudzbine\") " +
                        "|> filter(fn: (r) => r[\"narudzbinaid\"] == \"%s\") " +
                        "|> pivot(rowKey:[\"_time\"], columnKey:[\"_field\"], valueColumn:\"_value\") " +
                        "|> sort(columns:[\"_time\"])",
                bucket, narudzbinaid);
        return mapStatusPromene(client.getQueryApi(), flux);
    }

    /** Vraća sve evente određenog noviStatus u poslednjih N dana. */
    public List<PromenaStatusaPorudzbine> findAllByNoviStatus(InfluxDBClient client, String noviStatus, int days) {
        String flux = String.format(
                "from(bucket:\"%s\") " +
                        "|> range(start: -%dd) " +
                        "|> filter(fn: (r) => r[\"_measurement\"] == \"PromenaStatusaPorudzbine\") " +
                        "|> filter(fn: (r) => r[\"noviStatus\"] == \"%s\") " +
                        "|> pivot(rowKey:[\"_time\"], columnKey:[\"_field\"], valueColumn:\"_value\") " +
                        "|> sort(columns:[\"_time\"], desc: true)",
                bucket, days, noviStatus);
        return mapStatusPromene(client.getQueryApi(), flux);
    }

    private List<PromenaStatusaPorudzbine> mapStatusPromene(QueryApi queryApi, String flux) {
        List<PromenaStatusaPorudzbine> result = new ArrayList<>();
        for (FluxTable table : queryApi.query(flux)) {
            for (FluxRecord r : table.getRecords()) {
                PromenaStatusaPorudzbine m = new PromenaStatusaPorudzbine();
                m.setTimestamp((Instant) r.getValueByKey("_time"));
                m.setNarudzbinaid((String) r.getValueByKey("narudzbinaid"));
                m.setDobavljacid((String) r.getValueByKey("dobavljacid"));
                m.setDobavljacnaziv((String) r.getValueByKey("dobavljacnaziv"));
                m.setPrethodniStatus((String) r.getValueByKey("prethodniStatus"));
                m.setNoviStatus((String) r.getValueByKey("noviStatus"));
                Object min = r.getValueByKey("minuteUCekanju");
                if (min instanceof Number) m.setMinuteUCekanju(((Number) min).longValue());
                Object vr = r.getValueByKey("vrednostNarudzbine");
                if (vr instanceof Number) m.setVrednostNarudzbine(((Number) vr).doubleValue());
                Object br = r.getValueByKey("brojStavki");
                if (br instanceof Number) m.setBrojStavki(((Number) br).intValue());
                result.add(m);
            }
        }
        return result;
    }


    // MERENJE 2 -> CREATE

    public boolean saveBudzetPromena(InfluxDBClient client, PromenaBudzetaPoZanru m) {
        try {
            WriteApiBlocking writeApi = client.getWriteApiBlocking();
            if (m.getTimestamp() == null) m.setTimestamp(Instant.now());

            Point point = Point.measurement("PromenaBudzetaPoZanru")
                    .time(m.getTimestamp(), WritePrecision.MS)
                    .addTag("zanr",       m.getZanr())
                    .addTag("tipPromene", m.getTipPromene())
                    .addField("promenaStanja",     m.getPromenaStanja())
                    .addField("raspolozivoStanje", m.getRaspolozivoStanje());

            if (m.getUkupniBudzet() != null)
                point.addField("ukupniBudzet", m.getUkupniBudzet());
            if (m.getNapomena() != null)
                point.addField("napomena", m.getNapomena());

            writeApi.writePoint(point);
            return true;
        } catch (InfluxException e) {
            return false;
        }
    }

    //MERENJE 2 -> READ

    public List<PromenaBudzetaPoZanru> findBudzetByZanr(InfluxDBClient client, String zanr) {
        String flux = String.format(
                "from(bucket:\"%s\") " +
                        "|> range(start: 0) " +
                        "|> filter(fn: (r) => r[\"_measurement\"] == \"PromenaBudzetaPoZanru\") " +
                        "|> filter(fn: (r) => r[\"zanr\"] == \"%s\") " +
                        "|> pivot(rowKey:[\"_time\"], columnKey:[\"_field\"], valueColumn:\"_value\") " +
                        "|> sort(columns:[\"_time\"])",
                bucket, zanr);
        return mapBudzet(client.getQueryApi(), flux);
    }

    public List<PromenaBudzetaPoZanru> findBudzetByTipPromene(InfluxDBClient client, String tipPromene) {
        String flux = String.format(
                "from(bucket:\"%s\") " +
                        "|> range(start: 0) " +
                        "|> filter(fn: (r) => r[\"_measurement\"] == \"PromenaBudzetaPoZanru\") " +
                        "|> filter(fn: (r) => r[\"tipPromene\"] == \"%s\") " +
                        "|> pivot(rowKey:[\"_time\"], columnKey:[\"_field\"], valueColumn:\"_value\") " +
                        "|> sort(columns:[\"_time\"])",
                bucket, tipPromene);
        return mapBudzet(client.getQueryApi(), flux);
    }

    private List<PromenaBudzetaPoZanru> mapBudzet(QueryApi queryApi, String flux) {
        List<PromenaBudzetaPoZanru> result = new ArrayList<>();
        for (FluxTable table : queryApi.query(flux)) {
            for (FluxRecord r : table.getRecords()) {
                PromenaBudzetaPoZanru m = new PromenaBudzetaPoZanru();
                m.setTimestamp((Instant) r.getValueByKey("_time"));
                m.setZanr((String) r.getValueByKey("zanr"));
                m.setTipPromene((String) r.getValueByKey("tipPromene"));
                Object ps = r.getValueByKey("promenaStanja");
                if (ps instanceof Number) m.setPromenaStanja(((Number) ps).doubleValue());
                Object rs2 = r.getValueByKey("raspolozivoStanje");
                if (rs2 instanceof Number) m.setRaspolozivoStanje(((Number) rs2).doubleValue());
                Object ub = r.getValueByKey("ukupniBudzet");
                if (ub instanceof Number) m.setUkupniBudzet(((Number) ub).doubleValue());
                m.setNapomena((String) r.getValueByKey("napomena"));
                result.add(m);
            }
        }
        return result;
    }


    // MERENJE 3: PromenaPredlogaZaNabavku — CREATE
    // ================================================================

    public boolean savePredlogPromena(InfluxDBClient client, PromenaPredlogaZaNabavku m) {
        try {
            WriteApiBlocking writeApi = client.getWriteApiBlocking();
            if (m.getTimestamp() == null) m.setTimestamp(Instant.now());

            Point point = Point.measurement("PromenaPredlogaZaNabavku")
                    .time(m.getTimestamp(), WritePrecision.MS)
                    .addTag("predlogid", m.getPredlogid())
                    .addTag("zanr",      m.getZanr())
                    .addTag("status",    m.getStatus())
                    .addField("minuteUCekanju", m.getMinuteUCekanju())
                    .addField("procenjenaCena", m.getProcenjenaCena());

            if (m.getNaslovKnjige() != null)
                point.addField("naslovKnjige", m.getNaslovKnjige());

            writeApi.writePoint(point);
            return true;
        } catch (InfluxException e) {
            return false;
        }
    }

    // MERENJE 3  —> READ

    public List<PromenaPredlogaZaNabavku> findPredlogByPredlogid(InfluxDBClient client, String predlogid) {
        String flux = String.format(
                "from(bucket:\"%s\") " +
                        "|> range(start: 0) " +
                        "|> filter(fn: (r) => r[\"_measurement\"] == \"PromenaPredlogaZaNabavku\") " +
                        "|> filter(fn: (r) => r[\"predlogid\"] == \"%s\") " +
                        "|> pivot(rowKey:[\"_time\"], columnKey:[\"_field\"], valueColumn:\"_value\") " +
                        "|> sort(columns:[\"_time\"])",
                bucket, predlogid);
        return mapPredlog(client.getQueryApi(), flux);
    }

    public List<PromenaPredlogaZaNabavku> findPredlogByZanr(InfluxDBClient client, String zanr) {
        String flux = String.format(
                "from(bucket:\"%s\") " +
                        "|> range(start: 0) " +
                        "|> filter(fn: (r) => r[\"_measurement\"] == \"PromenaPredlogaZaNabavku\") " +
                        "|> filter(fn: (r) => r[\"zanr\"] == \"%s\") " +
                        "|> pivot(rowKey:[\"_time\"], columnKey:[\"_field\"], valueColumn:\"_value\") " +
                        "|> sort(columns:[\"_time\"])",
                bucket, zanr);
        return mapPredlog(client.getQueryApi(), flux);
    }

    private List<PromenaPredlogaZaNabavku> mapPredlog(QueryApi queryApi, String flux) {
        List<PromenaPredlogaZaNabavku> result = new ArrayList<>();
        for (FluxTable table : queryApi.query(flux)) {
            for (FluxRecord r : table.getRecords()) {
                PromenaPredlogaZaNabavku m = new PromenaPredlogaZaNabavku();
                m.setTimestamp((Instant) r.getValueByKey("_time"));
                m.setPredlogid((String) r.getValueByKey("predlogid"));
                m.setZanr((String) r.getValueByKey("zanr"));
                m.setStatus((String) r.getValueByKey("status"));
                Object min = r.getValueByKey("minuteUCekanju");
                if (min instanceof Number) m.setMinuteUCekanju(((Number) min).longValue());
                Object pc = r.getValueByKey("procenjenaCena");
                if (pc instanceof Number) m.setProcenjenaCena(((Number) pc).doubleValue());
                m.setNaslovKnjige((String) r.getValueByKey("naslovKnjige"));
                result.add(m);
            }
        }
        return result;
    }

    // SLOŽENI UPITI

    /**
     * Upit 1: Prosečno vreme isporuke (POSLATA->ISPORUCENA) po dobavljaču.
     * Vraća listu redova: dobavljacid, dobavljacnaziv, avgMinuteUCekanju.
     * Sortira po proseku (najbrži dobavljač prvi).
     */
    public List<FluxRecord> avgVremeIsporukePoDobavclja(InfluxDBClient client, int days) {
        String flux = String.format(
                "from(bucket:\"%s\") " +
                        "|> range(start: -%dd) " +
                        "|> filter(fn: (r) => r[\"_measurement\"] == \"PromenaStatusaPorudzbine\") " +
                        "|> filter(fn: (r) => r[\"noviStatus\"] == \"ISPORUCENA\") " +
                        "|> filter(fn: (r) => r[\"_field\"] == \"minuteUCekanju\") " +
                        "|> group(columns: [\"dobavljacid\", \"dobavljacnaziv\"]) " +
                        "|> mean() " +
                        "|> sort(columns: [\"_value\"])",
                bucket, days);
        return getRawRecords(client.getQueryApi(), flux);
    }

    /**
     * Upit 2: Dinamika trošenja budžeta po žanru, mesečno.
     * Filtrira samo NABAVKA tip, grupira po žanru i mesečnim prozorima.
     * Vraća sumu troška (promenaStanja je negativna, množimo sa -1).
     */
    public List<FluxRecord> budzetPoZanruMesecno(InfluxDBClient client, int months) {
        String flux = String.format(
                "from(bucket:\"%s\") " +
                        "|> range(start: -%dmo) " +
                        "|> filter(fn: (r) => r[\"_measurement\"] == \"PromenaBudzetaPoZanru\") " +
                        "|> filter(fn: (r) => r[\"tipPromene\"] == \"NABAVKA\") " +
                        "|> filter(fn: (r) => r[\"_field\"] == \"promenaStanja\") " +
                        "|> group(columns: [\"zanr\"]) " +
                        "|> aggregateWindow(every: 1mo, fn: sum, createEmpty: false) " +
                        "|> map(fn: (r) => ({r with trosak: r._value * -1.0})) " +
                        "|> sort(columns: [\"_time\"])",
                bucket, months);
        return getRawRecords(client.getQueryApi(), flux);
    }

    /**
     * Upit 3: Procenat odobrenih predloga po žanru.
     * Broji ukupne (NA_CEKANJU) i odobrene predloge po žanru.
     * Sortira po broju odobrenih (opadajuće).
     */
    public List<FluxRecord> odobreniPredloziPoZanru(InfluxDBClient client, int days) {
        String flux = String.format(
                "from(bucket:\"%s\") " +
                        "|> range(start: -%dd) " +
                        "|> filter(fn: (r) => r[\"_measurement\"] == \"PromenaPredlogaZaNabavku\") " +
                        "|> filter(fn: (r) => r[\"status\"] == \"ODOBREN\") " +
                        "|> filter(fn: (r) => r[\"_field\"] == \"procenjenaCena\") " +
                        "|> group(columns: [\"zanr\"]) " +
                        "|> count() " +
                        "|> sort(columns: [\"_value\"], desc: true)",
                bucket, days);
        return getRawRecords(client.getQueryApi(), flux);
    }

    /**
     * Upit 4 (bonus): Analiza otkazivanja narudžbina po dobavljaču.
     * Broji OTKAZANA evente, računa prosečno vreme čekanja pre otkazivanja.
     * Sortira po broju otkazanih (opadajuće).
     */
    public List<FluxRecord> otkazivanjePoDobavclja(InfluxDBClient client, int days) {
        String flux = String.format(
                "from(bucket:\"%s\") " +
                        "|> range(start: -%dd) " +
                        "|> filter(fn: (r) => r[\"_measurement\"] == \"PromenaStatusaPorudzbine\") " +
                        "|> filter(fn: (r) => r[\"noviStatus\"] == \"OTKAZANA\") " +
                        "|> filter(fn: (r) => r[\"_field\"] == \"minuteUCekanju\") " +
                        "|> group(columns: [\"dobavljacid\", \"dobavljacnaziv\"]) " +
                        "|> mean() " +
                        "|> sort(columns: [\"_value\"], desc: true)",
                bucket, days);
        return getRawRecords(client.getQueryApi(), flux);
    }

    private List<FluxRecord> getRawRecords(QueryApi queryApi, String flux) {
        List<FluxRecord> records = new ArrayList<>();
        for (FluxTable table : queryApi.query(flux))
            records.addAll(table.getRecords());
        return records;
    }

}
