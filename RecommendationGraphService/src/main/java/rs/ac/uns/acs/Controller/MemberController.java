package rs.ac.uns.acs.Controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.Service.MemberService;

import java.sql.Date;
import java.time.LocalDate;

@RestController
@RequestMapping("/members")
public class MemberController {

    private final MemberService memberService;

    public MemberController(MemberService service){
        this.memberService=service;
    }
    @PostMapping("/recommend")
    public ResponseEntity addRecommendation(
            @RequestParam Long memberId,
            @RequestParam String bookId,
            @RequestParam int rating) {

        memberService.addReccomendation(memberId, bookId, rating);
        return ResponseEntity.ok().build();
    }
    @PutMapping("/borrow")
    public ResponseEntity updateBorrow(
            @RequestParam Long memberId,
            @RequestParam String bookId,
            @RequestParam LocalDate date) {

        memberService.updateBorrowDate(memberId, bookId, date);
        return ResponseEntity.ok().build();
    }

}
