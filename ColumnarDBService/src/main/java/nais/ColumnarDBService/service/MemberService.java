package nais.ColumnarDBService.service;

import nais.ColumnarDBService.dto.MemberDTO;
import nais.ColumnarDBService.entity.Member;
import nais.ColumnarDBService.mapper.LibraryMapper;
import nais.ColumnarDBService.repository.MemberRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.CachePut;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class MemberService {

    @Autowired
    private MemberRepository memberRepository;

    @Autowired
    private LibraryMapper mapper;

    @CachePut(value = "members", key = "#result.memberId")
    public MemberDTO createMember(MemberDTO dto){
        dto.setMemberId(UUID.randomUUID());
        dto.setMembershipDate(LocalDateTime.now());
        dto.setActive(true);
        memberRepository.save(mapper.memberDTOToMember(dto));
        return dto;
    }

    @Cacheable(value = "members", key = "#memberId", condition = "#memberId !=null")
    public Optional<MemberDTO> getMemberById(UUID memberId){
        return memberRepository.findByMemberId(memberId).map(mapper::memberToMemberDTO);
    }
    public List<MemberDTO> getAllMembers() {
        return memberRepository.findAllMember()
                .stream()
                .map(mapper::memberToMemberDTO)
                .collect(Collectors.toList());
    }

    @CachePut(value = "members", key = "#dto.memberId")
    public MemberDTO updateMember(MemberDTO dto) {
        memberRepository.save(mapper.memberDTOToMember(dto));
        return dto;
    }

    @CacheEvict(value = "members", key = "#memberId")
    public void deleteMember(UUID memberId){
        Member member = new Member();
        member.setMemberId(memberId);
        memberRepository.delete(member);
    }
}
