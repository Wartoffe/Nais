package nais.ColumnarDBService.controller;

import nais.ColumnarDBService.dto.MemberDTO;
import nais.ColumnarDBService.service.MemberService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/members")
public class MemberController {

    @Autowired
    private MemberService memberService;

    @PostMapping
    public ResponseEntity<MemberDTO> createMember(@RequestBody MemberDTO dto){
        return new ResponseEntity<>(memberService.createMember(dto), HttpStatus.CREATED);
    }

    @GetMapping("/{memberId}")
    public ResponseEntity<MemberDTO> getMemberById(@PathVariable UUID memberId) {
        return memberService.getMemberById(memberId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
    @GetMapping
    public ResponseEntity<List<MemberDTO>> getAllMembers() {
        return ResponseEntity.ok(memberService.getAllMembers());
    }

    @PutMapping
    public ResponseEntity<MemberDTO> updateMember(@RequestBody MemberDTO dto) {
        return ResponseEntity.ok(memberService.updateMember(dto));
    }

    @DeleteMapping("/{memberId}")
    public ResponseEntity<Void> deleteMember(@PathVariable UUID memberId) {
        memberService.deleteMember(memberId);
        return ResponseEntity.noContent().build();
    }



}
