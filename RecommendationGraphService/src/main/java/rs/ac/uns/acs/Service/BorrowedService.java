package rs.ac.uns.acs.Service;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.Model.Book;
import rs.ac.uns.acs.Model.Borrow;
import rs.ac.uns.acs.Model.Member;
import rs.ac.uns.acs.Repository.BookRepository;
import rs.ac.uns.acs.Repository.MemberRepository;

import java.time.LocalDate;
import java.util.List;

@Service
public class BorrowedService {
    private final MemberRepository memberRepository;
    private final BookRepository bookRepository;
    public BorrowedService(MemberRepository memberRepository, BookRepository bookRepository){
        this.memberRepository=memberRepository;
        this.bookRepository=bookRepository;
    }
    private Member findMember(Long id) {
        return memberRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Member not found: " + id));
    }

    private Book findBook(String id) {
        return bookRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Book not found: " + id));
    }
    public Member borrow(Long memberId, String bookId, LocalDate date) {
        Member member = findMember(memberId);
        Book book = findBook(bookId);

        boolean alreadyBorrowed = member.getBorrowedBooks().stream()
                .anyMatch(b -> b.getBook().getId().equals(bookId));
        if (alreadyBorrowed) {
            throw new RuntimeException("Member " + memberId + " already has book " + bookId);
        }

        Borrow borrow = new Borrow();
        borrow.setBook(book);
        borrow.setDate(date != null ? date : LocalDate.now());

        member.getBorrowedBooks().add(borrow);
        return memberRepository.save(member);
    }
    public List<Borrow> readAll(Long memberId) {
        return findMember(memberId).getBorrowedBooks();
    }
    public Member updateDate(Long memberId, String bookId, LocalDate newDate) {
        Member member = findMember(memberId);
        Borrow borrow = member.getBorrowedBooks().stream()
                .filter(b -> b.getBook().getId().equals(bookId))
                .findFirst()
                .orElseThrow(() -> new RuntimeException(
                        "No BORROWED relationship between member " + memberId + " and book " + bookId));
        borrow.setDate(newDate);
        return memberRepository.save(member);
    }
    public Member returnBook(Long memberId, String bookId) {
        // Verify the relationship actually exists first
        findMember(memberId).getBorrowedBooks().stream()
                .filter(b -> b.getBook().getId().equals(bookId))
                .findFirst()
                .orElseThrow(() -> new RuntimeException(
                        "No BORROWED relationship between member " + memberId + " and book " + bookId));

        // Use explicit Cypher DELETE instead of collection manipulation —
        // @RelationshipProperties entities are NOT removed by save() alone
        memberRepository.deleteBorrowRelationship(memberId, bookId);

        return findMember(memberId);
    }
}
