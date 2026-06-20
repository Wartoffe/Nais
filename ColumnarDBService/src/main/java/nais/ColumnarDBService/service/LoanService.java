package nais.ColumnarDBService.service;

import nais.ColumnarDBService.dto.BookDTO;
import nais.ColumnarDBService.dto.LoanDTO;
import nais.ColumnarDBService.dto.ReturnDTO;
import nais.ColumnarDBService.dto.ReturnRequestDTO;
import nais.ColumnarDBService.entity.BookByGenre;
import nais.ColumnarDBService.entity.LoanByBook;
import nais.ColumnarDBService.entity.LoanByMember;
import nais.ColumnarDBService.entity.ReturnByDate;
import nais.ColumnarDBService.mapper.LibraryMapper;
import nais.ColumnarDBService.repository.BookByGenreRepository;
import nais.ColumnarDBService.repository.LoanByBookRepository;
import nais.ColumnarDBService.repository.LoanByMemberRepository;
import nais.ColumnarDBService.repository.ReturnByDateRepository;
import nais.ColumnarDBService.saga.SagaEventPublisher;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CachePut;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class LoanService {

    private static final Logger log = LoggerFactory.getLogger(LoanService.class);

    private static final int LOAN_PERIOD_DAYS = 14;

    @Autowired
    private LoanByMemberRepository loanByMemberRepository;

    @Autowired
    private LoanByBookRepository loanByBookRepository;

    @Autowired
    private BookByGenreRepository bookByGenreRepository;

    @Autowired
    private ReturnByDateRepository returnByDateRepository;

    @Autowired
    private LibraryMapper mapper;
    @Autowired
    private BookService bookService;
    @Autowired
    private SagaEventPublisher sagaEventPublisher;

    @CachePut(value = "loans", key = "#result.loanId")
    public LoanDTO createLoan(LoanDTO dto) {

        bookService.decreaseAvailableCopies(dto.getBookGenre(), dto.getBookTitle(), dto.getBookId());
        dto.setLoanId(UUID.randomUUID());
        dto.setLoanDate(LocalDateTime.now());
        dto.setDueDate(LocalDateTime.now().plusDays(LOAN_PERIOD_DAYS));
        dto.setReturned(false);
        dto.setLoanDurationDays(0);

        // From here on, availableCopies has already been decremented, so any
        // failure (including failing to publish the saga event) must roll
        // everything in this method back to leave Cassandra exactly as it
        // was before createLoan was called.
        try {
            LoanByMember loanByMember = mapper.loanDTOToLoanByMember(dto);
            loanByMemberRepository.save(loanByMember);
            LoanByBook loanByBook = mapper.loanDTOToLoanByBook(dto);
            loanByBookRepository.save(loanByBook);

            UUID bookUUID = dto.getBookId();
            BookByGenre book = bookByGenreRepository.findByBookId(bookUUID);

            // availableCopies was just decremented above (via
            // decreaseAvailableCopies); if it is now 0, this loan is the one
            // that took the last copy, so the book must disappear from
            // search results until a copy is returned.
            if (book.getAvailableCopies() == 0) {
                sagaEventPublisher.publishHideRequested(
                        book.getIsbn(), dto.getBookId(), dto.getBookTitle(), dto.getBookGenre(),
                        dto.getLoanId(), dto.getMemberId(), dto.getLoanDate());
            }
        } catch (RuntimeException ex) {
            log.warn("createLoan failed for member {} / book {}, rolling back: {}",
                    dto.getMemberId(), dto.getBookId(), ex.getMessage());
            compensateCreateLoan(dto.getMemberId(), dto.getLoanDate(), dto.getLoanId(), dto.getBookId(),
                    dto.getBookGenre(), dto.getBookTitle());
            throw new RuntimeException("Kreiranje pozajmice nije uspelo, izmene su povučene", ex);
        }

        return dto;
    }

    public List<LoanDTO> getLoansByMember(UUID memberId) {
        return loanByMemberRepository.findByMemberId(memberId)
                .stream()
                .map(mapper::loanByMemberToLoanDTO)
                .collect(Collectors.toList());
    }
    public List<LoanDTO> getLoansByBook(UUID bookId) {
        return loanByBookRepository.findByBookId(bookId)
                .stream()
                .map(mapper::loanByBookToLoanDTO)
                .collect(Collectors.toList());
    }
    @Cacheable(value = "loans", key = "#loanId", condition = "#loanId != null")
    public Optional<LoanDTO> getLoanById(UUID loanId) {
        return loanByMemberRepository.findAll()
                .stream()
                .filter(l -> l.getLoanId().equals(loanId))
                .findFirst()
                .map(mapper::loanByMemberToLoanDTO);
    }

    //nevracene pozajmice
    public List<LoanDTO> getActiveLoansByMember(UUID memberId) {
        return loanByMemberRepository.findActiveLoansByMember(memberId)
                .stream()
                .map(mapper::loanByMemberToLoanDTO)
                .collect(Collectors.toList());
    }

    public Long countLoansByMember(UUID memberId) {
        return loanByMemberRepository.countByMemberId(memberId);
    }

    public Double avgLoanDurationByMember(UUID memberId) {
        return loanByMemberRepository.avgLoanDurationByMember(memberId);
    }

    public Long countLoansByBook(UUID bookId) {
        return loanByBookRepository.countByBookId(bookId);
    }
    public ReturnDTO returnBook(ReturnRequestDTO request) {


        LocalDateTime now = LocalDateTime.now();
        String todayStr = LocalDate.now().toString();


        LoanByMember loanByMember = loanByMemberRepository
                .findByMemberId(request.getMemberId())
                .stream()
                .filter(l -> l.getLoanId().equals(request.getLoanId()))
                .findFirst()
                .orElseThrow(() -> new RuntimeException(
                        "Pozajmica nije pronađena za člana: " + request.getMemberId()));

        int durationDays = (int) ChronoUnit.DAYS.between(loanByMember.getLoanDate(), now);
        UUID bookUUID= request.getBookId();
        BookByGenre book= bookByGenreRepository.findByBookId(bookUUID);

        // Captured BEFORE availableCopies is incremented below: if the book
        // currently has zero available copies, this particular return is
        // the one that brings it back into circulation, so Elasticsearch
        // needs to unhide it once the increment actually happens.
        boolean shouldUnhide = (book.getAvailableCopies() == 0);
        String isbn = book.getIsbn();

        boolean copiesIncreased = false;
        try {
            loanByMember.setReturned(true);
            loanByMember.setReturnDate(now);
            loanByMember.setLoanDurationDays(durationDays);
            loanByMemberRepository.save(loanByMember);


            bookService.increaseAvailableCopies(loanByMember.getBookGenre(), loanByMember.getBookTitle(), loanByMember.getBookId());
            copiesIncreased = true;

            loanByBookRepository.findByBookId(request.getBookId())
                    .stream()
                    .filter(l -> l.getLoanId().equals(request.getLoanId()))
                    .findFirst()
                    .ifPresent(loanByBook -> {
                        loanByBook.setReturned(true);
                        loanByBook.setReturnDate(now);
                        loanByBookRepository.save(loanByBook);
                    });


            ReturnByDate returnByDate = new ReturnByDate();
            returnByDate.setReturnDate(todayStr);
            returnByDate.setReturnTimestamp(now);
            returnByDate.setLoanId(request.getLoanId());
            returnByDate.setMemberId(request.getMemberId());
            returnByDate.setMemberName(loanByMember.getMemberId().toString()); // overwrite u init
            returnByDate.setBookId(request.getBookId());
            returnByDate.setBookTitle(loanByMember.getBookTitle());
            returnByDate.setBookGenre(loanByMember.getBookGenre());
            returnByDate.setLoanDate(loanByMember.getLoanDate());
            returnByDate.setLoanDurationDays(durationDays);
            returnByDateRepository.save(returnByDate);

            ReturnDTO result = mapper.returnByDateToReturnDTO(returnByDate);

            if (shouldUnhide) {
                sagaEventPublisher.publishUnhideRequested(
                        isbn, request.getBookId(), loanByMember.getBookTitle(), loanByMember.getBookGenre(),
                        request.getLoanId(), request.getMemberId(), loanByMember.getLoanDate(),
                        todayStr, now);
            }

            return result;
        } catch (RuntimeException ex) {
            log.warn("returnBook failed for member {} / loan {}, rolling back: {}",
                    request.getMemberId(), request.getLoanId(), ex.getMessage());

            // Local rollback: only undo what actually happened above. The
            // loanByMember object already in scope is reverted in place;
            // the available-copies increment is only undone if it actually
            // ran (guarded by copiesIncreased) so we never double-decrement
            // a count that was never incremented in the first place.
            try {
                loanByMember.setReturned(false);
                loanByMember.setReturnDate(null);
                loanByMember.setLoanDurationDays(0);
                loanByMemberRepository.save(loanByMember);
            } catch (RuntimeException rollbackEx) {
                log.warn("Failed to roll back loanByMember for loan {}: {}", request.getLoanId(), rollbackEx.getMessage());
            }

            if (copiesIncreased) {
                try {
                    bookService.decreaseAvailableCopies(loanByMember.getBookGenre(), loanByMember.getBookTitle(), loanByMember.getBookId());
                } catch (RuntimeException rollbackEx) {
                    log.warn("Failed to roll back availableCopies for book {}: {}", request.getBookId(), rollbackEx.getMessage());
                }
            }

            try {
                loanByBookRepository.findByBookId(request.getBookId())
                        .stream()
                        .filter(l -> l.getLoanId().equals(request.getLoanId()))
                        .findFirst()
                        .ifPresent(loanByBook -> {
                            loanByBook.setReturned(false);
                            loanByBook.setReturnDate(null);
                            loanByBookRepository.save(loanByBook);
                        });
            } catch (RuntimeException rollbackEx) {
                log.warn("Failed to roll back loanByBook for loan {}: {}", request.getLoanId(), rollbackEx.getMessage());
            }

            try {
                returnByDateRepository.deleteReturn(todayStr, now, request.getLoanId());
            } catch (RuntimeException rollbackEx) {
                log.warn("Failed to roll back returnByDate for loan {}: {}", request.getLoanId(), rollbackEx.getMessage());
            }

            throw new RuntimeException("Vraćanje knjige nije uspelo, izmene su povučene", ex);
        }
    }

    public void deleteLoan(UUID memberId, LocalDateTime loanDate, UUID loanId,
                           UUID bookId) {
        loanByMemberRepository.deleteLoan(memberId, loanDate, loanId);
        loanByBookRepository.deleteLoan(bookId, loanDate, loanId);
    }

    public List<LoanDTO> getLoansByDateRange(LocalDate from, LocalDate to) {
        LocalDateTime fromDT = from.atStartOfDay();
        LocalDateTime toDT   = to.atTime(23, 59, 59);

        return loanByMemberRepository.findAll()
                .stream()
                .filter(l -> l.getLoanDate() != null
                        && !l.getLoanDate().isBefore(fromDT)
                        && !l.getLoanDate().isAfter(toDT))
                .map(mapper::loanByMemberToLoanDTO)
                .collect(Collectors.toList());
    }

    // ── Saga compensation ──────────────────────────────────────────────────
    //
    // Both methods below fully reverse a createLoan/returnBook that already
    // committed locally. They are invoked from two places:
    //  1. Internally, right after a local failure during createLoan/
    //     returnBook itself (see the catch blocks above).
    //  2. By BookVisibilitySagaListener, when the search service reports
    //     that it could not hide/unhide the corresponding book
    //     (HIDE_FAILED / UNHIDE_FAILED) -- at that point createLoan/
    //     returnBook had already returned successfully to the caller, so
    //     this is the only way to undo it.
    //
    // Deletes against Cassandra are idempotent (deleting a row that isn't
    // there is a no-op), so it's always safe to issue them even if the
    // corresponding save never actually happened.

    /**
     * Reverses a createLoan: restores the available-copies count and
     * removes the loan records that were created for it.
     */
    public void compensateCreateLoan(UUID memberId, LocalDateTime loanDate, UUID loanId, UUID bookId,
                                      String bookGenre, String bookTitle) {
        try {
            bookService.increaseAvailableCopies(bookGenre, bookTitle, bookId);
        } catch (RuntimeException ex) {
            log.warn("Compensation: failed to restore availableCopies for book {}: {}", bookId, ex.getMessage());
        }
        try {
            loanByMemberRepository.deleteLoan(memberId, loanDate, loanId);
        } catch (RuntimeException ex) {
            log.warn("Compensation: failed to delete loanByMember for loan {}: {}", loanId, ex.getMessage());
        }
        try {
            loanByBookRepository.deleteLoan(bookId, loanDate, loanId);
        } catch (RuntimeException ex) {
            log.warn("Compensation: failed to delete loanByBook for loan {}: {}", loanId, ex.getMessage());
        }
    }

    /**
     * Reverses a returnBook: puts the loan back into its "active" (not
     * returned) state, removes the return record that was created, and
     * undoes the available-copies increment.
     */
    public void compensateReturnBook(UUID memberId, UUID loanId, UUID bookId, String bookGenre, String bookTitle,
                                      String returnDate, LocalDateTime returnTimestamp) {
        try {
            loanByMemberRepository.findByMemberId(memberId).stream()
                    .filter(l -> l.getLoanId().equals(loanId))
                    .findFirst()
                    .ifPresent(loanByMember -> {
                        loanByMember.setReturned(false);
                        loanByMember.setReturnDate(null);
                        loanByMember.setLoanDurationDays(0);
                        loanByMemberRepository.save(loanByMember);
                    });
        } catch (RuntimeException ex) {
            log.warn("Compensation: failed to revert loanByMember for loan {}: {}", loanId, ex.getMessage());
        }

        try {
            loanByBookRepository.findByBookId(bookId).stream()
                    .filter(l -> l.getLoanId().equals(loanId))
                    .findFirst()
                    .ifPresent(loanByBook -> {
                        loanByBook.setReturned(false);
                        loanByBook.setReturnDate(null);
                        loanByBookRepository.save(loanByBook);
                    });
        } catch (RuntimeException ex) {
            log.warn("Compensation: failed to revert loanByBook for loan {}: {}", loanId, ex.getMessage());
        }

        if (returnDate != null && returnTimestamp != null) {
            try {
                returnByDateRepository.deleteReturn(returnDate, returnTimestamp, loanId);
            } catch (RuntimeException ex) {
                log.warn("Compensation: failed to delete returnByDate for loan {}: {}", loanId, ex.getMessage());
            }
        }

        try {
            bookService.decreaseAvailableCopies(bookGenre, bookTitle, bookId);
        } catch (RuntimeException ex) {
            log.warn("Compensation: failed to undo availableCopies increment for book {}: {}", bookId, ex.getMessage());
        }
    }

}
