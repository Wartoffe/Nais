package rs.ac.uns.acs.nais.GraphDatabaseService.config;

import org.neo4j.driver.Driver;
import org.neo4j.driver.Session;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
public class DataSeeder implements CommandLineRunner {

    private final Driver driver;

    public DataSeeder(Driver driver) {
        this.driver = driver;
    }

    @Override
    public void run(String... args) throws Exception {
        try (Session session = driver.session()) {

            long count = session.run("MATCH (n) RETURN count(n) AS cnt")
                    .single().get("cnt").asLong();

            if (count > 0) {
                System.out.println("[DataSeeder] Baza vec ima podatke, preskacemo seed.");
                return;
            }

            System.out.println("[DataSeeder] Punimo bazu test podacima...");

            session.run("""
                // === ZANROVI ===
                CREATE (z1:Zanr {naziv: 'Fantastika', opis: 'Epska i high fantasy literatura'})
                CREATE (z2:Zanr {naziv: 'Romantika', opis: 'Ljubavni romani i drame'})
                CREATE (z3:Zanr {naziv: 'Triler', opis: 'Napete price, krimici i misterije'})
                CREATE (z4:Zanr {naziv: 'Licni razvoj', opis: 'Knjige o produktivnosti i razvoju licnosti'})

                // === TRENDOVI ===
                CREATE (t1:Trend {naziv: 'BookTok Fantastika', period: '2024-Q1', score: 95})
                CREATE (t2:Trend {naziv: 'Dark Romance', period: '2024-Q2', score: 90})
                CREATE (t3:Trend {naziv: 'Bestseler trileri', period: '2024-Q1', score: 80})

                // === KNJIGE ===
                CREATE (k1:Knjiga {isbn: '978-0-7432-7356-5', naziv: 'A Game of Thrones', autor: 'George R.R. Martin', godinaIzdavanja: 1996, cena: 1800.0})
                CREATE (k2:Knjiga {isbn: '978-0-06-112008-4', naziv: 'To Kill a Mockingbird', autor: 'Harper Lee', godinaIzdavanja: 1960, cena: 1200.0})
                CREATE (k3:Knjiga {isbn: '978-1-5011-4885-6', naziv: 'The Way of Kings', autor: 'Brandon Sanderson', godinaIzdavanja: 2010, cena: 2200.0})
                CREATE (k4:Knjiga {isbn: '978-1-63557-214-4', naziv: 'Fourth Wing', autor: 'Rebecca Yarros', godinaIzdavanja: 2023, cena: 2500.0})
                CREATE (k5:Knjiga {isbn: '978-1-5290-4955-2', naziv: 'A Court of Thorns and Roses', autor: 'Sarah J. Maas', godinaIzdavanja: 2015, cena: 2000.0})
                CREATE (k6:Knjiga {isbn: '978-0-385-54734-9', naziv: 'The Cruel Prince', autor: 'Holly Black', godinaIzdavanja: 2018, cena: 1700.0})
                CREATE (k7:Knjiga {isbn: '978-0-525-55360-5', naziv: 'It Ends with Us', autor: 'Colleen Hoover', godinaIzdavanja: 2016, cena: 1600.0})
                CREATE (k8:Knjiga {isbn: '978-1-250-31747-4', naziv: 'Verity', autor: 'Colleen Hoover', godinaIzdavanja: 2018, cena: 1900.0})
                CREATE (k9:Knjiga {isbn: '978-0-385-54368-6', naziv: 'Gone Girl', autor: 'Gillian Flynn', godinaIzdavanja: 2012, cena: 1500.0})
                CREATE (k10:Knjiga {isbn: '978-1-250-30169-5', naziv: 'The Silent Patient', autor: 'Alex Michaelides', godinaIzdavanja: 2019, cena: 1800.0})
                CREATE (k11:Knjiga {isbn: '978-0-7352-1136-1', naziv: 'Atomic Habits', autor: 'James Clear', godinaIzdavanja: 2018, cena: 2100.0})
                CREATE (k12:Knjiga {isbn: '978-0-06-266231-4', naziv: 'The 48 Laws of Power', autor: 'Robert Greene', godinaIzdavanja: 1998, cena: 2300.0})

                // === KORISNICI ===
                CREATE (u1:Korisnik {email: 'marko.petrovic@uns.ac.rs', ime: 'Marko', prezime: 'Petrovic', tipKorisnika: 'student'})
                CREATE (u2:Korisnik {email: 'ana.jovic@uns.ac.rs', ime: 'Ana', prezime: 'Jovic', tipKorisnika: 'student'})
                CREATE (u3:Korisnik {email: 'ivan.nikolic@ftn.uns.ac.rs', ime: 'Ivan', prezime: 'Nikolic', tipKorisnika: 'nastavnik'})
                CREATE (u4:Korisnik {email: 'milica.stojanovic@gmail.com', ime: 'Milica', prezime: 'Stojanovic', tipKorisnika: 'clan'})
                CREATE (u5:Korisnik {email: 'petar.djordjevic@gmail.com', ime: 'Petar', prezime: 'Djordjevic', tipKorisnika: 'clan'})

                // === KNJIGA PRIPADA ZANRU ===
                CREATE (k1)-[:PRIPADA]->(z1)
                CREATE (k3)-[:PRIPADA]->(z1)
                CREATE (k4)-[:PRIPADA]->(z1)
                CREATE (k5)-[:PRIPADA]->(z1)
                CREATE (k6)-[:PRIPADA]->(z1)
                CREATE (k2)-[:PRIPADA]->(z3)
                CREATE (k7)-[:PRIPADA]->(z2)
                CREATE (k8)-[:PRIPADA]->(z2)
                CREATE (k9)-[:PRIPADA]->(z3)
                CREATE (k10)-[:PRIPADA]->(z3)
                CREATE (k11)-[:PRIPADA]->(z4)
                CREATE (k12)-[:PRIPADA]->(z4)

                // === KNJIGA JE_TREND ===
                CREATE (k4)-[:JE_TREND {relevantnostScore: 98.0}]->(t1)
                CREATE (k5)-[:JE_TREND {relevantnostScore: 92.0}]->(t1)
                CREATE (k3)-[:JE_TREND {relevantnostScore: 85.0}]->(t1)
                CREATE (k1)-[:JE_TREND {relevantnostScore: 75.0}]->(t1)
                CREATE (k7)-[:JE_TREND {relevantnostScore: 96.0}]->(t2)
                CREATE (k8)-[:JE_TREND {relevantnostScore: 88.0}]->(t2)
                CREATE (k5)-[:JE_TREND {relevantnostScore: 82.0}]->(t2)
                CREATE (k6)-[:JE_TREND {relevantnostScore: 78.0}]->(t2)
                CREATE (k10)-[:JE_TREND {relevantnostScore: 85.0}]->(t3)
                CREATE (k9)-[:JE_TREND {relevantnostScore: 72.0}]->(t3)

                // === KORISNIK ZAINTERESOVAN_ZA KNJIGU ===
                CREATE (u1)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-01-15'), brojZahteva: 3}]->(k1)
                CREATE (u1)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-01-20'), brojZahteva: 2}]->(k3)
                CREATE (u1)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-02-01'), brojZahteva: 1}]->(k6)
                CREATE (u2)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-01-10'), brojZahteva: 4}]->(k7)
                CREATE (u2)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-01-25'), brojZahteva: 3}]->(k8)
                CREATE (u2)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-02-05'), brojZahteva: 2}]->(k5)
                CREATE (u3)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-01-05'), brojZahteva: 5}]->(k11)
                CREATE (u3)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-01-18'), brojZahteva: 3}]->(k12)
                CREATE (u3)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-02-10'), brojZahteva: 2}]->(k9)
                CREATE (u4)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-01-12'), brojZahteva: 2}]->(k4)
                CREATE (u4)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-01-22'), brojZahteva: 4}]->(k5)
                CREATE (u4)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-02-08'), brojZahteva: 1}]->(k6)
                CREATE (u5)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-01-08'), brojZahteva: 2}]->(k9)
                CREATE (u5)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-01-30'), brojZahteva: 3}]->(k10)
                CREATE (u5)-[:ZAINTERESOVAN_ZA {datumZahteva: date('2024-02-15'), brojZahteva: 1}]->(k2)
            """);

            System.out.println("[DataSeeder] Uspesno kreirano: 4 zanra, 3 trenda, 12 knjiga, 5 korisnika sa vezama!");
        }
    }
}
