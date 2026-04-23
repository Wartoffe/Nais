package rs.ac.uns.acs.Controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.Model.Borrow;
import rs.ac.uns.acs.Model.Member;
import rs.ac.uns.acs.Service.BorrowedService;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/borrowed")
public class BorrowedController {
    private final BorrowedService borrowedService;
    public BorrowedController(BorrowedService borrowedService){
        this.borrowedService=borrowedService;
    }
    @PostMapping("/member/{memberId}/book/{bookId}")
    public ResponseEntity<Member> borrow(
            @PathVariable Long memberId,
            @PathVariable String bookId,
            @RequestBody(required = false) Map<String, String> body) {
        LocalDate date = (body != null && body.containsKey("date"))
                ? LocalDate.parse(body.get("date"))
                : null;
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(borrowedService.borrow(memberId, bookId, date));
    }
    @GetMapping("/member/{memberId}")
    public ResponseEntity<List<Borrow>> readAll(@PathVariable Long memberId) {
        return ResponseEntity.ok(borrowedService.readAll(memberId));
    }
    @PutMapping("/member/{memberId}/book/{bookId}")
    public ResponseEntity<Member> updateDate(
            @PathVariable Long memberId,
            @PathVariable String bookId,
            @RequestBody Map<String, String> body) {
        LocalDate newDate = LocalDate.parse(body.get("date"));
        return ResponseEntity.ok(borrowedService.updateDate(memberId, bookId, newDate));
    }
    @DeleteMapping("/member/{memberId}/book/{bookId}")
    public ResponseEntity<Member> returnBook(
            @PathVariable Long memberId,
            @PathVariable String bookId) {
        return ResponseEntity.ok(borrowedService.returnBook(memberId, bookId));
    }
}
