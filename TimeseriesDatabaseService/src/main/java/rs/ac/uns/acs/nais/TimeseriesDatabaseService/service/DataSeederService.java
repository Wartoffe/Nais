package rs.ac.uns.acs.nais.TimeseriesDatabaseService.service;

import com.influxdb.client.InfluxDBClient;
import com.influxdb.client.WriteApiBlocking;
import com.influxdb.client.domain.WritePrecision;
import com.influxdb.client.write.Point;
import org.springframework.stereotype.Service;
import rs.ac.uns.acs.nais.TimeseriesDatabaseService.configuration.InfluxDBConnectionClass;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Puni bazu test podacima — minimum 2000 slogova po merenju.
 *
 * Poziv: POST /library-influx/seed/all
 *
 * Merenje 1 — PromenaStatusaPorudzbine:
 *   600 narudžbina × ~3-4 eventa = ~2200 slogova
 *
 * Merenje 2 — PromenaBudzetaPoZanru:
 *   24 meseca × 7 žanrova × ~13 nabavki + povraćaji = ~2500 slogova
 *
 * Merenje 3 — PromenaPredlogaZaNabavku:
 *   1200 predloga × ~1.85 eventa = ~2200 slogova
 */
@Service
public class DataSeederService {

    private final InfluxDBConnectionClass conn;
    private final Random rng = new Random(42);

    private static final String[][] DOBAVLJACI = {
        {"DOB-001", "Vulkan Izdavastvo"},
        {"DOB-002", "Laguna"},
        {"DOB-003", "Dereta"},
        {"DOB-004", "Klett"},
        {"DOB-005", "BigZ"},
        {"DOB-006", "Zavod za udzbenike"},
        {"DOB-007", "Prosveta"},
        {"DOB-008", "Stylos"}
    };

    private static final String[] ZANROVI = {
        "FIKCIJA", "NON_FIKCIJA", "DECA", "AKADEMSKO", "PERIODIKA", "POEZIJA", "DRAMA"
    };

    private static final String[] NASLOVI = {
        "1984", "Zlocin i kazna", "Mali Princ", "Brace Karamazovi",
        "Ana Karenjina", "Proces", "Stranac", "Gospoda Bovari",
        "Don Kihot", "Hamlet", "Beda", "Idiot", "Majstor i Margarita",
        "Starac i more", "Veliki Getsbi", "Ponos i predrasuda",
        "Kad su cvetale tikve", "Dervis i smrt", "Na Drini cuprija"
    };

    public DataSeederService(InfluxDBConnectionClass conn) {
        this.conn = conn;
    }

    // ================================================================
    // SEED ALL
    // ================================================================
    public String seedAll() {
        int s1 = seedStatusPromene();
        int s2 = seedBudzetPromene();
        int s3 = seedPredlogPromene();
        return String.format(
            "Seeding zavrseno: PromenaStatusaPorudzbine=%d, PromenaBudzetaPoZanru=%d, PromenaPredlogaZaNabavku=%d, UKUPNO=%d",
            s1, s2, s3, s1 + s2 + s3);
    }

    // ================================================================
    // SEEDER 1: PromenaStatusaPorudzbine — ~2200 slogova
    // ================================================================
    public int seedStatusPromene() {
        InfluxDBClient client = conn.buildConnection();
        WriteApiBlocking writeApi = client.getWriteApiBlocking();
        List<Point> batch = new ArrayList<>();
        int ukupno = 0;

        for (int i = 1; i <= 600; i++) {
            String narudzbinaid = String.format("NAR-%04d", i);
            String[] dob = DOBAVLJACI[rng.nextInt(DOBAVLJACI.length)];
            String zanr = ZANROVI[rng.nextInt(ZANROVI.length)];
            double vrednost = 5000 + rng.nextDouble() * 95000;
            int stavki = 5 + rng.nextInt(50);

            Instant kreirano = Instant.now()
                    .minus(rng.nextInt(500), ChronoUnit.DAYS)
                    .minus(rng.nextInt(23), ChronoUnit.HOURS);

            // EVENT 1: KREIRANA (minuteUCekanju = 0)
            batch.add(Point.measurement("PromenaStatusaPorudzbine")
                    .time(kreirano, WritePrecision.MS)
                    .addTag("narudzbinaid",    narudzbinaid)
                    .addTag("dobavljacid",     dob[0])
                    .addTag("dobavljacnaziv",  dob[1])
                    .addTag("prethodniStatus", "NONE")
                    .addTag("noviStatus",      "KREIRANA")
                    .addField("minuteUCekanju",     0L)
                    .addField("vrednostNarudzbine", vrednost)
                    .addField("brojStavki",         stavki));

            // EVENT 2: POSLATA (1–5 dana posle)
            long minKreiranja = 60L * 24 * (1 + rng.nextInt(5));
            Instant poslato = kreirano.plus(minKreiranja, ChronoUnit.MINUTES);
            batch.add(Point.measurement("PromenaStatusaPorudzbine")
                    .time(poslato, WritePrecision.MS)
                    .addTag("narudzbinaid",    narudzbinaid)
                    .addTag("dobavljacid",     dob[0])
                    .addTag("dobavljacnaziv",  dob[1])
                    .addTag("prethodniStatus", "KREIRANA")
                    .addTag("noviStatus",      "POSLATA")
                    .addField("minuteUCekanju",     minKreiranja)
                    .addField("vrednostNarudzbine", vrednost)
                    .addField("brojStavki",         stavki));

            // EVENT 3: ISPORUCENA ili OTKAZANA
            boolean otkazana = rng.nextDouble() < 0.08;
            if (otkazana) {
                long minPre = 60L * (2 + rng.nextInt(48));
                Instant otkazano = poslato.plus(minPre, ChronoUnit.MINUTES);
                batch.add(Point.measurement("PromenaStatusaPorudzbine")
                        .time(otkazano, WritePrecision.MS)
                        .addTag("narudzbinaid",    narudzbinaid)
                        .addTag("dobavljacid",     dob[0])
                        .addTag("dobavljacnaziv",  dob[1])
                        .addTag("prethodniStatus", "POSLATA")
                        .addTag("noviStatus",      "OTKAZANA")
                        .addField("minuteUCekanju",     minPre)
                        .addField("vrednostNarudzbine", vrednost)
                        .addField("brojStavki",         stavki));
            } else {
                long minIsporuke = 60L * 24 * (3 + rng.nextInt(18));
                Instant isporuceno = poslato.plus(minIsporuke, ChronoUnit.MINUTES);
                batch.add(Point.measurement("PromenaStatusaPorudzbine")
                        .time(isporuceno, WritePrecision.MS)
                        .addTag("narudzbinaid",    narudzbinaid)
                        .addTag("dobavljacid",     dob[0])
                        .addTag("dobavljacnaziv",  dob[1])
                        .addTag("prethodniStatus", "POSLATA")
                        .addTag("noviStatus",      "ISPORUCENA")
                        .addField("minuteUCekanju",     minIsporuke)
                        .addField("vrednostNarudzbine", vrednost)
                        .addField("brojStavki",         stavki));
            }

            ukupno += batch.size();
            if (batch.size() >= 300) {
                writeApi.writePoints(batch);
                batch.clear();
            }
        }

        if (!batch.isEmpty()) writeApi.writePoints(batch);
        client.close();
        return ukupno;
    }

    // ================================================================
    // SEEDER 2: PromenaBudzetaPoZanru — ~2500 slogova
    // ================================================================
    public int seedBudzetPromene() {
        InfluxDBClient client = conn.buildConnection();
        WriteApiBlocking writeApi = client.getWriteApiBlocking();
        List<Point> batch = new ArrayList<>();
        int ukupno = 0;

        double[] stanje = new double[ZANROVI.length];
        double[] ukupni = new double[ZANROVI.length];
        for (int z = 0; z < ZANROVI.length; z++) {
            stanje[z] = 200_000 + rng.nextDouble() * 300_000;
            ukupni[z] = stanje[z];
        }

        for (int mesec = 24; mesec >= 0; mesec--) {
            Instant pocetakMeseca = Instant.now().minus(mesec * 30L, ChronoUnit.DAYS);

            for (int z = 0; z < ZANROVI.length; z++) {
                int nabavki = 8 + rng.nextInt(8);

                for (int n = 0; n < nabavki; n++) {
                    double iznos = 3000 + rng.nextDouble() * 47000;
                    stanje[z] -= iznos;

                    // korekcija ako stanje padne ispod 10%
                    if (stanje[z] < ukupni[z] * 0.1) {
                        double dopuna = ukupni[z] * 0.5;
                        stanje[z] += dopuna;
                        Instant ts = pocetakMeseca.plus(rng.nextInt(28), ChronoUnit.DAYS);
                        batch.add(Point.measurement("PromenaBudzetaPoZanru")
                                .time(ts, WritePrecision.MS)
                                .addTag("zanr",       ZANROVI[z])
                                .addTag("tipPromene", "KOREKCIJA_BUDZETA")
                                .addField("promenaStanja",     dopuna)
                                .addField("raspolozivoStanje", stanje[z])
                                .addField("ukupniBudzet",      ukupni[z])
                                .addField("napomena",          "Dopuna budzeta"));
                        ukupno++;
                    }

                    Instant ts = pocetakMeseca
                            .plus(rng.nextInt(28), ChronoUnit.DAYS)
                            .plus(rng.nextInt(23), ChronoUnit.HOURS);
                    batch.add(Point.measurement("PromenaBudzetaPoZanru")
                            .time(ts, WritePrecision.MS)
                            .addTag("zanr",       ZANROVI[z])
                            .addTag("tipPromene", "NABAVKA")
                            .addField("promenaStanja",     -iznos)
                            .addField("raspolozivoStanje", stanje[z])
                            .addField("ukupniBudzet",      ukupni[z]));
                    ukupno++;

                    // ~10% šansa povraćaj
                    if (rng.nextDouble() < 0.10) {
                        double povracaj = iznos * (0.3 + rng.nextDouble() * 0.7);
                        stanje[z] += povracaj;
                        Instant tsPov = ts.plus(1 + rng.nextInt(5), ChronoUnit.DAYS);
                        batch.add(Point.measurement("PromenaBudzetaPoZanru")
                                .time(tsPov, WritePrecision.MS)
                                .addTag("zanr",       ZANROVI[z])
                                .addTag("tipPromene", "POVRACAJ")
                                .addField("promenaStanja",     povracaj)
                                .addField("raspolozivoStanje", stanje[z])
                                .addField("ukupniBudzet",      ukupni[z])
                                .addField("napomena",          "Povracaj zbog ostecenja"));
                        ukupno++;
                    }
                }
            }

            if (batch.size() >= 300) {
                writeApi.writePoints(batch);
                batch.clear();
            }
        }

        if (!batch.isEmpty()) writeApi.writePoints(batch);
        client.close();
        return ukupno;
    }

    // ================================================================
    // SEEDER 3: PromenaPredlogaZaNabavku — ~2200 slogova
    // ================================================================
    public int seedPredlogPromene() {
        InfluxDBClient client = conn.buildConnection();
        WriteApiBlocking writeApi = client.getWriteApiBlocking();
        List<Point> batch = new ArrayList<>();
        int ukupno = 0;

        for (int i = 1; i <= 1200; i++) {
            String predlogid = String.format("PRE-%04d", i);
            String zanr = ZANROVI[rng.nextInt(ZANROVI.length)];
            String naslov = NASLOVI[rng.nextInt(NASLOVI.length)];
            double cena = 1500 + rng.nextDouble() * 48500;

            Instant kreirano = Instant.now()
                    .minus(rng.nextInt(400), ChronoUnit.DAYS)
                    .minus(rng.nextInt(23), ChronoUnit.HOURS);

            // EVENT 1: NA_CEKANJU (minuteUCekanju = 0)
            batch.add(Point.measurement("PromenaPredlogaZaNabavku")
                    .time(kreirano, WritePrecision.MS)
                    .addTag("predlogid", predlogid)
                    .addTag("zanr",      zanr)
                    .addTag("status",    "NA_CEKANJU")
                    .addField("minuteUCekanju", 0L)
                    .addField("procenjenaCena", cena)
                    .addField("naslovKnjige",   naslov));
            ukupno++;

            // 85% dobija odluku
            if (rng.nextDouble() < 0.85) {
                long minCekanja = 60L * 24 * (1 + rng.nextInt(30));
                Instant odluceno = kreirano.plus(minCekanja, ChronoUnit.MINUTES);
                String odluka = rng.nextDouble() < 0.65 ? "ODOBREN" : "ODBIJEN";
                batch.add(Point.measurement("PromenaPredlogaZaNabavku")
                        .time(odluceno, WritePrecision.MS)
                        .addTag("predlogid", predlogid)
                        .addTag("zanr",      zanr)
                        .addTag("status",    odluka)
                        .addField("minuteUCekanju", minCekanja)
                        .addField("procenjenaCena", cena)
                        .addField("naslovKnjige",   naslov));
                ukupno++;
            }

            if (batch.size() >= 300) {
                writeApi.writePoints(batch);
                batch.clear();
            }
        }

        if (!batch.isEmpty()) writeApi.writePoints(batch);
        client.close();
        return ukupno;
    }
}
