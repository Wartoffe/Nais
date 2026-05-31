package nais.ColumnarDBService.entity;

import org.springframework.data.cassandra.core.cql.Ordering;
import org.springframework.data.cassandra.core.cql.PrimaryKeyType;
import org.springframework.data.cassandra.core.mapping.Column;
import org.springframework.data.cassandra.core.mapping.PrimaryKeyColumn;
import org.springframework.data.cassandra.core.mapping.Table;

import java.time.LocalDateTime;
import java.util.UUID;

@Table("loans_by_member")
public class LoanByMember {

    @PrimaryKeyColumn(name="member_id", type= PrimaryKeyType.PARTITIONED)
    private UUID memberId;

    //da mi se najnovije pozajmice prikazuju prve
    @PrimaryKeyColumn(name = "loan_date", ordinal = 0, ordering = Ordering.DESCENDING)
    private LocalDateTime loanDate;

    @PrimaryKeyColumn(name = "loan_id", ordinal = 1, ordering = Ordering.ASCENDING)
    private UUID loanId;
    @Column("book_id")
    private UUID bookId;

    @Column("book_title")
    private String bookTitle;

    @Column("book_genre")
    private String bookGenre;

    @Column("due_date")
    private LocalDateTime dueDate;

    @Column("return_date")
    private LocalDateTime returnDate;

    @Column("is_returned")
    private boolean returned;

    @Column("loan_duration_days")
    private int loanDurationDays;

    public LoanByMember() {
    }

    public LoanByMember(UUID memberId, LocalDateTime loanDate, UUID loanId, UUID bookId, String bookTitle, String bookGenre, LocalDateTime dueDate, LocalDateTime returnDate, boolean returned, int loanDurationDays) {
        this.memberId = memberId;
        this.loanDate = loanDate;
        this.loanId = loanId;
        this.bookId = bookId;
        this.bookTitle = bookTitle;
        this.bookGenre = bookGenre;
        this.dueDate = dueDate;
        this.returnDate = returnDate;
        this.returned = returned;
        this.loanDurationDays = loanDurationDays;
    }

    public UUID getMemberId() {
        return memberId;
    }

    public void setMemberId(UUID memberId) {
        this.memberId = memberId;
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

    public int getLoanDurationDays() {
        return loanDurationDays;
    }

    public void setLoanDurationDays(int loanDurationDays) {
        this.loanDurationDays = loanDurationDays;
    }
}
