package nais.ColumnarDBService.entity;

import org.springframework.data.cassandra.core.cql.PrimaryKeyType;
import org.springframework.data.cassandra.core.mapping.Column;
import org.springframework.data.cassandra.core.mapping.PrimaryKeyColumn;
import org.springframework.data.cassandra.core.mapping.Table;

import java.time.LocalDateTime;
import java.util.UUID;

@Table("members")
public class Member {

    //particionise se po jmbg
    @PrimaryKeyColumn(name = "member_id", type = PrimaryKeyType.PARTITIONED)
    private UUID memberId;

    @Column("ime_i_prezime")
    private String fullName;
    @Column("email")
    private String email;

    @Column("phone")
    private String phone;

    @Column("membership_date")
    private LocalDateTime membershipDate;

    @Column("is_active")
    private boolean active;

    public Member() {
    }

    public Member(UUID memberId, String fullName, String email, String phone, LocalDateTime membershipDate, boolean active) {
        this.memberId = memberId;
        this.fullName = fullName;
        this.email = email;
        this.phone = phone;
        this.membershipDate = membershipDate;
        this.active = active;
    }

    public UUID getMemberId() {
        return memberId;
    }

    public void setMemberId(UUID memberId) {
        this.memberId = memberId;
    }

    public String getFullName() {
        return fullName;
    }

    public void setFullName(String fullName) {
        this.fullName = fullName;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    public LocalDateTime getMembershipDate() {
        return membershipDate;
    }

    public void setMembershipDate(LocalDateTime membershipDate) {
        this.membershipDate = membershipDate;
    }

    public boolean isActive() {
        return active;
    }

    public void setActive(boolean active) {
        this.active = active;
    }
}
