package nais.ColumnarDBService.entity;

import org.springframework.data.cassandra.core.cql.Ordering;
import org.springframework.data.cassandra.core.cql.PrimaryKeyType;
import org.springframework.data.cassandra.core.mapping.Column;
import org.springframework.data.cassandra.core.mapping.PrimaryKeyColumn;
import org.springframework.data.cassandra.core.mapping.Table;

import java.time.LocalDateTime;
import java.util.UUID;

@Table("loans_by_book")
public class LoanByBook {
    @PrimaryKeyColumn(name = "book_id", type = PrimaryKeyType.PARTITIONED)
    private UUID bookId;

    @PrimaryKeyColumn(name = "loan_date", ordinal = 0, ordering = Ordering.DESCENDING)
    private LocalDateTime loanDate;

    @PrimaryKeyColumn(name = "loan_id", ordinal = 1, ordering = Ordering.ASCENDING)
    private UUID loanId;
    @Column("member_id")
    private UUID memberId;

    @Column("member_name")
    private String memberName;

    @Column("book_title")
    private String bookTitle;

    @Column("due_date")
    private LocalDateTime dueDate;

    @Column("return_date")
    private LocalDateTime returnDate;

    @Column("is_returned")
    private boolean returned;

    public LoanByBook() {
    }

    public LoanByBook(UUID bookId, LocalDateTime loanDate, UUID loanId, UUID memberId, String memberName, String bookTitle, LocalDateTime dueDate, LocalDateTime returnDate, boolean returned) {
        this.bookId = bookId;
        this.loanDate = loanDate;
        this.loanId = loanId;
        this.memberId = memberId;
        this.memberName = memberName;
        this.bookTitle = bookTitle;
        this.dueDate = dueDate;
        this.returnDate = returnDate;
        this.returned = returned;
    }

    public UUID getBookId() {
        return bookId;
    }

    public void setBookId(UUID bookId) {
        this.bookId = bookId;
    }

    public LocalDateTime getLoanDate() {
        return loanDate;
    }

    public void setLoanDate(LocalDateTime loanDate) {
        this.loanDate = loanDate;
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

    public String getBookTitle() {
        return bookTitle;
    }

    public void setBookTitle(String bookTitle) {
        this.bookTitle = bookTitle;
    }

    public LocalDateTime getDueDate() {
        return dueDate;
    }

    public void setDueDate(LocalDateTime dueDate) {
        this.dueDate = dueDate;
    }

    public LocalDateTime getReturnDate() {
        return returnDate;
    }

    public void setReturnDate(LocalDateTime returnDate) {
        this.returnDate = returnDate;
    }

    public boolean isReturned() {
        return returned;
    }

    public void setReturned(boolean returned) {
        this.returned = returned;
    }
}
