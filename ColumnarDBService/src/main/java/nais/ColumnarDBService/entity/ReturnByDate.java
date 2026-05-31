package nais.ColumnarDBService.entity;

import org.springframework.data.cassandra.core.cql.Ordering;
import org.springframework.data.cassandra.core.cql.PrimaryKeyType;
import org.springframework.data.cassandra.core.mapping.Column;
import org.springframework.data.cassandra.core.mapping.PrimaryKeyColumn;
import org.springframework.data.cassandra.core.mapping.Table;

import java.time.LocalDateTime;
import java.util.UUID;

@Table("returns_by_date")
public class ReturnByDate {
    @PrimaryKeyColumn(name = "return_date", type = PrimaryKeyType.PARTITIONED)
    private String returnDate;

    @PrimaryKeyColumn(name = "return_timestamp", ordinal = 0, ordering = Ordering.DESCENDING)
    private LocalDateTime returnTimestamp;

    @PrimaryKeyColumn(name = "loan_id", ordinal = 1, ordering = Ordering.ASCENDING)
    private UUID loanId;

    @Column("member_id")
    private UUID memberId;

    @Column("member_name")
    private String memberName;

    @Column("book_id")
    private UUID bookId;

    @Column("book_title")
    private String bookTitle;

    @Column("book_genre")
    private String bookGenre;

    @Column("loan_date")
    private LocalDateTime loanDate;

    @Column("loan_duration_days")
    private int loanDurationDays;

    public ReturnByDate() {
    }

    public ReturnByDate(String returnDate, LocalDateTime returnTimestamp, UUID loanId, UUID memberId, String memberName, UUID bookId, String bookTitle, String bookGenre, LocalDateTime loanDate, int loanDurationDays) {
        this.returnDate = returnDate;
        this.returnTimestamp = returnTimestamp;
        this.loanId = loanId;
        this.memberId = memberId;
        this.memberName = memberName;
        this.bookId = bookId;
        this.bookTitle = bookTitle;
        this.bookGenre = bookGenre;
        this.loanDate = loanDate;
        this.loanDurationDays = loanDurationDays;
    }

    public String getReturnDate() {
        return returnDate;
    }

    public void setReturnDate(String returnDate) {
        this.returnDate = returnDate;
    }

    public LocalDateTime getReturnTimestamp() {
        return returnTimestamp;
    }

    public void setReturnTimestamp(LocalDateTime returnTimestamp) {
        this.returnTimestamp = returnTimestamp;
    }

    public UUID getLoanId() {
        return loanId;
    }

    public void setLoanId(UUID loanId) {
        this.loanId = loanId;
    }

    public UUID getMemberId() {
        return memberId;
    }

    public void setMemberId(UUID memberId) {
        this.memberId = memberId;
    }

    public String getMemberName() {
        return memberName;
    }

    public void setMemberName(String memberName) {
        this.memberName = memberName;
    }

    public UUID getBookId() {
        return bookId;
    }

    public void setBookId(UUID bookId) {
        this.bookId = bookId;
    }

    public String getBookTitle() {
        return bookTitle;
    }

    public void setBookTitle(String bookTitle) {
        this.bookTitle = bookTitle;
    }

    public String getBookGenre() {
        return bookGenre;
    }

    public void setBookGenre(String bookGenre) {
        this.bookGenre = bookGenre;
    }

    public LocalDateTime getLoanDate() {
        return loanDate;
    }

    public void setLoanDate(LocalDateTime loanDate) {
        this.loanDate = loanDate;
    }

    public int getLoanDurationDays() {
        return loanDurationDays;
    }

    public void setLoanDurationDays(int loanDurationDays) {
        this.loanDurationDays = loanDurationDays;
    }
}
