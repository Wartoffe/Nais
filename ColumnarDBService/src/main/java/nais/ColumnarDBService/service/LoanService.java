package nais.ColumnarDBService.service;

import nais.ColumnarDBService.dto.LoanDTO;
import nais.ColumnarDBService.dto.ReturnDTO;
import nais.ColumnarDBService.dto.ReturnRequestDTO;
import nais.ColumnarDBService.entity.LoanByBook;
import nais.ColumnarDBService.entity.LoanByMember;
import nais.ColumnarDBService.entity.ReturnByDate;
import nais.ColumnarDBService.mapper.LibraryMapper;
import nais.ColumnarDBService.repository.LoanByBookRepository;
import nais.ColumnarDBService.repository.LoanByMemberRepository;
import nais.ColumnarDBService.repository.ReturnByDateRepository;
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

    private static final int LOAN_PERIOD_DAYS = 14;

    @Autowired
    private LoanByMemberRepository loanByMemberRepository;

    @Autowired
    private LoanByBookRepository loanByBookRepository;

    @Autowired
    private ReturnByDateRepository returnByDateRepository;

    @Autowired
    private LibraryMapper mapper;

    @CachePut(value = "loans", key = "#result.loanId")
    public LoanDTO createLoan(LoanDTO dto) {
        dto.setLoanId(UUID.randomUUID());
        dto.setLoanDate(LocalDateTime.now());
        dto.setDueDate(LocalDateTime.now().plusDays(LOAN_PERIOD_DAYS));
        dto.setReturned(false);
        dto.setLoanDurationDays(0);

        LoanByMember loanByMember = mapper.loanDTOToLoanByMember(dto);
        loanByMemberRepository.save(loanByMember);
        LoanByBook loanByBook = mapper.loanDTOToLoanByBook(dto);
        loanByBookRepository.save(loanByBook);

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


        loanByMember.setReturned(true);
        loanByMember.setReturnDate(now);
        loanByMember.setLoanDurationDays(durationDays);
        loanByMemberRepository.save(loanByMember);


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

        return mapper.returnByDateToReturnDTO(returnByDate);
    }

    public void deleteLoan(UUID memberId, LocalDateTime loanDate, UUID loanId,
                           UUID bookId) {
        loanByMemberRepository.deleteLoan(memberId, loanDate, loanId);
        loanByBookRepository.deleteLoan(bookId, loanDate, loanId);
    }

}
