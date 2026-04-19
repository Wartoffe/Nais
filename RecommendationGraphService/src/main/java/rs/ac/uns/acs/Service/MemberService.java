package rs.ac.uns.acs.Service;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.Repository.MemberRepository;

import java.sql.Date;

@Service
public class MemberService {
    private final MemberRepository memberRepository;

    public MemberService(MemberRepository memberRepository){
        this.memberRepository=memberRepository;
    }
    public void addReccomendation(Long memberId, String bookId, int rating){
        memberRepository.addOrUpdateRecommendation(memberId, bookId, rating);
    }

    public void updateBorrowDate(Long memberId, String bookId, Date date){
        memberRepository.updateBorrowDate(memberId, bookId, date);
    }
}
