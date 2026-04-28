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

    public void delete(Long id) {
        Member member = findById(id);
        memberRepository.delete(member);
    }
}
