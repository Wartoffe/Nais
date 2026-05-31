package nais.ColumnarDBService.init;

import nais.ColumnarDBService.entity.*;
import nais.ColumnarDBService.repository.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;
import java.util.List;

@Component
public class DataInitializer {
    private static final Logger log = LoggerFactory.getLogger(DataInitializer.class);

    @Autowired private MemberRepository memberRepository;
    @Autowired private BookByGenreRepository bookByGenreRepository;
    @Autowired private LoanByMemberRepository loanByMemberRepository;
    @Autowired private LoanByBookRepository loanByBookRepository;
    @Autowired
    private ReturnByDateRepository returnByDateRepository;

    // ─── Fiksirani UUID-ovi za reproducibilnost ───────────────────────────────

    private static final UUID M1 = UUID.fromString("10000000-0000-0000-0000-000000000001");
    private static final UUID M2 = UUID.fromString("10000000-0000-0000-0000-000000000002");
    private static final UUID M3 = UUID.fromString("10000000-0000-0000-0000-000000000003");
    private static final UUID M4 = UUID.fromString("10000000-0000-0000-0000-000000000004");
    private static final UUID M5 = UUID.fromString("10000000-0000-0000-0000-000000000005");

    private static final UUID B1 = UUID.fromString("20000000-0000-0000-0000-000000000001");
    private static final UUID B2 = UUID.fromString("20000000-0000-0000-0000-000000000002");
    private static final UUID B3 = UUID.fromString("20000000-0000-0000-0000-000000000003");
    private static final UUID B4 = UUID.fromString("20000000-0000-0000-0000-000000000004");
    private static final UUID B5 = UUID.fromString("20000000-0000-0000-0000-000000000005");
    private static final UUID B6 = UUID.fromString("20000000-0000-0000-0000-000000000006");
    private static final UUID B7 = UUID.fromString("20000000-0000-0000-0000-000000000007");
    private static final UUID B8 = UUID.fromString("20000000-0000-0000-0000-000000000008");

    private static final UUID L1  = UUID.fromString("30000000-0000-0000-0000-000000000001");
    private static final UUID L2  = UUID.fromString("30000000-0000-0000-0000-000000000002");
    private static final UUID L3  = UUID.fromString("30000000-0000-0000-0000-000000000003");
    private static final UUID L4  = UUID.fromString("30000000-0000-0000-0000-000000000004");
    private static final UUID L5  = UUID.fromString("30000000-0000-0000-0000-000000000005");
    private static final UUID L6  = UUID.fromString("30000000-0000-0000-0000-000000000006");
    private static final UUID L7  = UUID.fromString("30000000-0000-0000-0000-000000000007");
    private static final UUID L8  = UUID.fromString("30000000-0000-0000-0000-000000000008");
    private static final UUID L9  = UUID.fromString("30000000-0000-0000-0000-000000000009");
    private static final UUID L10 = UUID.fromString("30000000-0000-0000-0000-000000000010");

    @EventListener(ApplicationReadyEvent.class)
    public void init() {
        // Preskaci ako podaci vec postoje
        if (!memberRepository.findAllMember().isEmpty()) {
            log.info("Test podaci već postoje — inicijalizacija preskočena.");
            return;
        }
        log.info("Pokretanje inicijalizacije test podataka...");

        insertMembers();
        insertBooks();
        insertLoansAndReturns();

        log.info("Inicijalizacija završena: 5 članova, 8 knjiga, 10 pozajmica, 5 vraćanja.");
    }

    // ─── Članovi ─────────────────────────────────────────────────────────────

    private void insertMembers() {
        memberRepository.saveAll(List.of(
                member(M1, "Ana Marković",    "ana.markovic@email.com",    "+381601234567",
                        LocalDateTime.of(2022, 1, 15, 10, 0), true),
                member(M2, "Petar Jović",     "petar.jovic@email.com",     "+381602345678",
                        LocalDateTime.of(2022, 3, 20, 12, 0), true),
                member(M3, "Milena Stanić",   "milena.stanic@email.com",   "+381603456789",
                        LocalDateTime.of(2023, 5, 10,  9, 0), true),
                member(M4, "Jovan Ilić",      "jovan.ilic@email.com",      "+381604567890",
                        LocalDateTime.of(2023, 8, 1,  11, 0), true),
                member(M5, "Dragana Nikolić", "dragana.nikolic@email.com", "+381605678901",
                        LocalDateTime.of(2024, 2, 28, 14, 0), false)
        ));
        log.info("  ✓ Upisano 5 članova");
    }

    // ─── Knjige ───────────────────────────────────────────────────────────────

    private void insertBooks() {
        // Žanr: Roman
        bookByGenreRepository.saveAll(List.of(
                book(B1, "Roman", "Na Drini ćuprija",       "Ivo Andrić",        "978-86-17-00001-1", 1945, 5, 3),
                book(B2, "Roman", "Derviš i smrt",           "Meša Selimović",    "978-86-17-00002-2", 1966, 4, 2),
                book(B3, "Roman", "Gospodar prstenova",      "J.R.R. Tolkien",    "978-86-17-00003-3", 1954, 6, 4)
        ));

        // Žanr: Naučna fantastika
        bookByGenreRepository.saveAll(List.of(
                book(B4, "Naucna fantastika", "Dina",          "Frank Herbert",  "978-86-17-00004-4", 1965, 4, 2),
                book(B5, "Naucna fantastika", "Kraj vecnosti", "Isaac Asimov",   "978-86-17-00005-5", 1955, 3, 3),
                book(B6, "Naucna fantastika", "Neuromanser",   "William Gibson", "978-86-17-00006-6", 1984, 3, 1)
        ));

        // Žanr: Istorija
        bookByGenreRepository.saveAll(List.of(
                book(B7, "Istorija", "Sapiens",                  "Yuval Noah Harari", "978-86-17-00007-7", 2011, 5, 3),
                book(B8, "Istorija", "Kratka istorija vremena",  "Stephen Hawking",   "978-86-17-00008-8", 1988, 4, 2)
        ));

        log.info("  ✓ Upisano 8 knjiga u 3 žanra");
    }

    // ─── Pozajmice i vraćanja ─────────────────────────────────────────────────

    private void insertLoansAndReturns() {
        String today = LocalDate.now().toString();

        // --- Vraćene pozajmice (5 komada) ---

        // L1: Ana pozajmila "Na Drini ćuprija", vraćena posle 12 dana
        LocalDateTime l1Date = LocalDateTime.now().minusDays(30);
        LocalDateTime l1Return = l1Date.plusDays(12);
        saveLoan(L1, M1, "Ana Marković",   B1, "Na Drini cuprija",      "Roman",
                l1Date, l1Date.plusDays(14), l1Return, true, 12);
        saveReturn(L1, M1, "Ana Marković",   B1, "Na Drini cuprija",    "Roman",
                l1Return.toLocalDate().toString(), l1Return, l1Date, 12);

        // L2: Petar pozajmio "Dina", vraćena posle 10 dana
        LocalDateTime l2Date = LocalDateTime.now().minusDays(25);
        LocalDateTime l2Return = l2Date.plusDays(10);
        saveLoan(L2, M2, "Petar Jović",    B4, "Dina",                  "Naucna fantastika",
                l2Date, l2Date.plusDays(14), l2Return, true, 10);
        saveReturn(L2, M2, "Petar Jović",    B4, "Dina",                "Naucna fantastika",
                l2Return.toLocalDate().toString(), l2Return, l2Date, 10);

        // L3: Milena pozajmila "Sapiens", vraćena posle 7 dana
        LocalDateTime l3Date = LocalDateTime.now().minusDays(20);
        LocalDateTime l3Return = l3Date.plusDays(7);
        saveLoan(L3, M3, "Milena Stanić",  B7, "Sapiens",               "Istorija",
                l3Date, l3Date.plusDays(14), l3Return, true, 7);
        saveReturn(L3, M3, "Milena Stanić",  B7, "Sapiens",             "Istorija",
                l3Return.toLocalDate().toString(), l3Return, l3Date, 7);

        // L4: Ana pozajmila "Derviš i smrt", vraćena posle 14 dana
        LocalDateTime l4Date = LocalDateTime.now().minusDays(18);
        LocalDateTime l4Return = l4Date.plusDays(14);
        saveLoan(L4, M1, "Ana Marković",   B2, "Dervis i smrt",         "Roman",
                l4Date, l4Date.plusDays(14), l4Return, true, 14);
        saveReturn(L4, M1, "Ana Marković",   B2, "Dervis i smrt",       "Roman",
                l4Return.toLocalDate().toString(), l4Return, l4Date, 14);

        // L5: Jovan pozajmio "Kraj večnosti", vraćena danas
        LocalDateTime l5Date = LocalDateTime.now().minusDays(8);
        LocalDateTime l5Return = LocalDateTime.now().minusHours(2);
        saveLoan(L5, M4, "Jovan Ilić",     B5, "Kraj vecnosti",         "Naucna fantastika",
                l5Date, l5Date.plusDays(14), l5Return, true, 8);
        saveReturn(L5, M4, "Jovan Ilić",     B5, "Kraj vecnosti",       "Naucna fantastika",
                today, l5Return, l5Date, 8);

        // --- Aktivne pozajmice (5 komada, nije vraćeno) ---

        // L6: Petar čita "Gospodar prstenova"
        LocalDateTime l6Date = LocalDateTime.now().minusDays(5);
        saveLoan(L6, M2, "Petar Jović",    B3, "Gospodar prstenova",    "Roman",
                l6Date, l6Date.plusDays(14), null, false, 0);

        // L7: Milena čita "Neuromanser"
        LocalDateTime l7Date = LocalDateTime.now().minusDays(3);
        saveLoan(L7, M3, "Milena Stanić",  B6, "Neuromanser",           "Naucna fantastika",
                l7Date, l7Date.plusDays(14), null, false, 0);

        // L8: Ana čita "Kratka istorija vremena"
        LocalDateTime l8Date = LocalDateTime.now().minusDays(2);
        saveLoan(L8, M1, "Ana Marković",   B8, "Kratka istorija vremena","Istorija",
                l8Date, l8Date.plusDays(14), null, false, 0);

        // L9: Jovan čita "Na Drini ćuprija" (knjiga ponovo pozajmljena)
        LocalDateTime l9Date = LocalDateTime.now().minusDays(1);
        saveLoan(L9, M4, "Jovan Ilić",     B1, "Na Drini cuprija",      "Roman",
                l9Date, l9Date.plusDays(14), null, false, 0);

        // L10: Petar čita "Sapiens"
        LocalDateTime l10Date = LocalDateTime.now().minusHours(5);
        saveLoan(L10, M2, "Petar Jović",   B7, "Sapiens",               "Istorija",
                l10Date, l10Date.plusDays(14), null, false, 0);

        log.info("  ✓ Upisano 10 pozajmica (5 završenih, 5 aktivnih)");
        log.info("  ✓ Upisano 5 vraćanja");
    }

    // ─── Pomocne fabričke metode ──────────────────────────────────────────────

    private Member member(UUID id, String name, String email, String phone,
                          LocalDateTime date, boolean active) {
        Member m = new Member();
        m.setMemberId(id);
        m.setFullName(name);
        m.setEmail(email);
        m.setPhone(phone);
        m.setMembershipDate(date);
        m.setActive(active);
        return m;
    }

    private BookByGenre book(UUID id, String genre, String title, String author,
                             String isbn, int year, int total, int available) {
        BookByGenre b = new BookByGenre();
        b.setBookId(id);
        b.setGenre(genre);
        b.setTitle(title);
        b.setAuthor(author);
        b.setIsbn(isbn);
        b.setPublishedYear(year);
        b.setTotalCopies(total);
        b.setAvailableCopies(available);
        return b;
    }

    private void saveLoan(UUID loanId, UUID memberId, String memberName,
                          UUID bookId, String bookTitle, String bookGenre,
                          LocalDateTime loanDate, LocalDateTime dueDate,
                          LocalDateTime returnDate, boolean returned, int durationDays) {
        // Upis u loans_by_member
        LoanByMember lbm = new LoanByMember();
        lbm.setLoanId(loanId);
        lbm.setMemberId(memberId);
        lbm.setBookId(bookId);
        lbm.setBookTitle(bookTitle);
        lbm.setBookGenre(bookGenre);
        lbm.setLoanDate(loanDate);
        lbm.setDueDate(dueDate);
        lbm.setReturnDate(returnDate);
        lbm.setReturned(returned);
        lbm.setLoanDurationDays(durationDays);
        loanByMemberRepository.save(lbm);

        // Upis u loans_by_book
        LoanByBook lbb = new LoanByBook();
        lbb.setLoanId(loanId);
        lbb.setBookId(bookId);
        lbb.setBookTitle(bookTitle);
        lbb.setMemberId(memberId);
        lbb.setMemberName(memberName);
        lbb.setLoanDate(loanDate);
        lbb.setDueDate(dueDate);
        lbb.setReturnDate(returnDate);
        lbb.setReturned(returned);
        loanByBookRepository.save(lbb);
    }

    private void saveReturn(UUID loanId, UUID memberId, String memberName,
                            UUID bookId, String bookTitle, String bookGenre,
                            String returnDate, LocalDateTime returnTimestamp,
                            LocalDateTime loanDate, int durationDays) {
        ReturnByDate r = new ReturnByDate();
        r.setLoanId(loanId);
        r.setReturnDate(returnDate);
        r.setReturnTimestamp(returnTimestamp);
        r.setMemberId(memberId);
        r.setMemberName(memberName);
        r.setBookId(bookId);
        r.setBookTitle(bookTitle);
        r.setBookGenre(bookGenre);
        r.setLoanDate(loanDate);
        r.setLoanDurationDays(durationDays);
        returnByDateRepository.save(r);
    }
}
