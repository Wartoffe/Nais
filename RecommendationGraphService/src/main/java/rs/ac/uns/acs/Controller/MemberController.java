package rs.ac.uns.acs.Controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.Model.Member;
import rs.ac.uns.acs.Service.MemberService;

import java.sql.Date;
import java.time.LocalDate;
import java.util.List;

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
    @PostMapping
    public ResponseEntity<Member> create(@RequestBody Member member) {
        return ResponseEntity.status(HttpStatus.CREATED).body(memberService.create(member));
    }

    @GetMapping
    public ResponseEntity<List<Member>> findAll() {
        return ResponseEntity.ok(memberService.findAll());
    }
    @PutMapping("/{id}")
    public ResponseEntity<Member> update(@PathVariable Long id, @RequestBody Member member) {
        return ResponseEntity.ok(memberService.update(id, member));
    }
    /*
    @PostMapping("/{id}/borrow/{bookId}")
    public ResponseEntity<Member> borrowBook(
            @PathVariable Long id,
            @PathVariable String bookId) {
        return ResponseEntity.ok(memberService.borrowBook(id, bookId));
    }
    @DeleteMapping("/{id}/borrow/{bookId}")
    public ResponseEntity<Member> returnBook(
            @PathVariable Long id,
            @PathVariable String bookId) {
        return ResponseEntity.ok(memberService.returnBook(id, bookId));
    }*/
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        memberService.delete(id);
        return ResponseEntity.noContent().build();
    }

}
