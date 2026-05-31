package nais.ColumnarDBService.controller;

import nais.ColumnarDBService.dto.LoanDTO;
import nais.ColumnarDBService.dto.MemberDTO;
import nais.ColumnarDBService.dto.ReturnDTO;
import nais.ColumnarDBService.dto.ReturnRequestDTO;
import nais.ColumnarDBService.service.LoanService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/loans")
public class LoanController {
    @Autowired
    private LoanService loanService;

    @PostMapping
    public ResponseEntity<LoanDTO> createLoan(@RequestBody LoanDTO dto) {
        return new ResponseEntity<>(loanService.createLoan(dto), HttpStatus.CREATED);
    }

    //sve pozajmice jednog clana
    @GetMapping("/member/{memberId}")
    public ResponseEntity<List<LoanDTO>> getLoansByMember(@PathVariable UUID memberId) {
        return ResponseEntity.ok(loanService.getLoansByMember(memberId));
    }

    //istorija pozajmica za knjigu
    @GetMapping("/book/{bookId}")
    public ResponseEntity<List<LoanDTO>> getLoansByBook(@PathVariable UUID bookId) {
        return ResponseEntity.ok(loanService.getLoansByBook(bookId));
    }

    //dohvata pozajmicu
    @GetMapping("/{loanId}")
    public ResponseEntity<LoanDTO> getLoanById(@PathVariable UUID loanId) {
        return loanService.getLoanById(loanId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    //nevracene pozajmice jednog clana
    @GetMapping("/member/{memberId}/active")
    public ResponseEntity<List<LoanDTO>> getActiveLoansByMember(@PathVariable UUID memberId) {
        return ResponseEntity.ok(loanService.getActiveLoansByMember(memberId));
    }

    //ukupan broj pozajmica nekog clana
    @GetMapping("/member/{memberId}/count")
    public ResponseEntity<Long> countLoansByMember(@PathVariable UUID memberId) {
        return ResponseEntity.ok(loanService.countLoansByMember(memberId));
    }

    //prosecno trajanje zavrsenih pozajmica
    @GetMapping("/member/{memberId}/avg-duration")
    public ResponseEntity<Double> avgLoanDurationByMember(@PathVariable UUID memberId) {
        return ResponseEntity.ok(loanService.avgLoanDurationByMember(memberId));
    }

    //ukupan broj pozajmica knjige
    @GetMapping("/book/{bookId}/count")
    public ResponseEntity<Long> countLoansByBook(@PathVariable UUID bookId) {
        return ResponseEntity.ok(loanService.countLoansByBook(bookId));
    }
    //vracanje knjige
    @PostMapping("/return")
    public ResponseEntity<ReturnDTO> returnBook(@RequestBody ReturnRequestDTO request) {
        return ResponseEntity.ok(loanService.returnBook(request));
    }
    @DeleteMapping
    public ResponseEntity<Void> deleteLoan(@RequestParam UUID memberId,
                                           @RequestParam String loanDate,
                                           @RequestParam UUID loanId,
                                           @RequestParam UUID bookId) {
        loanService.deleteLoan(memberId, LocalDateTime.parse(loanDate), loanId, bookId);
        return ResponseEntity.noContent().build();
    }


}
