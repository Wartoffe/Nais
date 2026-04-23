package rs.ac.uns.acs.Service;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.Model.Book;
import rs.ac.uns.acs.Model.Borrow;
import rs.ac.uns.acs.Model.Member;
import rs.ac.uns.acs.Repository.BookRepository;
import rs.ac.uns.acs.Repository.MemberRepository;

import java.sql.Date;
import java.time.LocalDate;
import java.util.List;

@Service
public class MemberService {
    private final MemberRepository memberRepository;
    private final BookRepository bookRepository;
    public MemberService(MemberRepository memberRepository, BookRepository bookRepository){
        this.memberRepository=memberRepository;
        this.bookRepository=bookRepository;
    }
    public void addReccomendation(Long memberId, String bookId, int rating){
        memberRepository.addOrUpdateRecommendation(memberId, bookId, rating);
    }

    public void updateBorrowDate(Long memberId, String bookId, LocalDate date){
        memberRepository.updateBorrowDate(memberId, bookId, date);
    }
    public Member create(Member member) {
        return memberRepository.save(member);
    }
    public List<Member> findAll() {
        return memberRepository.findAll();
    }
    public Member findById(Long id) {
        return memberRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Member not found with id: " + id));
    }
    public Member update(Long id, Member updated) {
        Member existing = findById(id);
        existing.setFirstName(updated.getFirstName());
        existing.setLastName(updated.getLastName());
        existing.setAge(updated.getAge());
        return memberRepository.save(existing);
    }
    public Member borrowBook(Long memberId, String bookId) {
        Member member = findById(memberId);
        Book book = bookRepository.findById(bookId)
                .orElseThrow(() -> new RuntimeException("Book not found with id: " + bookId));

        Borrow borrow = new Borrow();
        borrow.setBook(book);
        borrow.setDate(LocalDate.now());

        member.getBorrowedBooks().add(borrow);
        return memberRepository.save(member);
    }
    public Member returnBook(Long memberId, String bookId) {
        Member member = findById(memberId);
        member.getBorrowedBooks().removeIf(b -> b.getBook().getId().equals(bookId));
        return memberRepository.save(member);
    }
    public void delete(Long id) {
        Member member = findById(id);
        memberRepository.delete(member);
    }
}
