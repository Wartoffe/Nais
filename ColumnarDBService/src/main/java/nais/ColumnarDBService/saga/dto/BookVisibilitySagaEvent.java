package nais.ColumnarDBService.saga.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.annotation.JsonSerialize;
import com.fasterxml.jackson.datatype.jsr310.deser.LocalDateTimeDeserializer;
import com.fasterxml.jackson.datatype.jsr310.ser.LocalDateTimeSerializer;

import java.time.LocalDateTime;
import java.util.UUID;

public class BookVisibilitySagaEvent {

    private UUID sagaId;
    private SagaEventType eventType;
    private String isbn;
    private UUID bookId;
    private String bookTitle;
    private String bookGenre;
    private UUID loanId;
    private UUID memberId;

    @JsonSerialize(using = LocalDateTimeSerializer.class)
    @JsonDeserialize(using = LocalDateTimeDeserializer.class)
    @JsonFormat(shape = JsonFormat.Shape.STRING)
    private LocalDateTime loanDate;

    // samo za vracanje knjige
    private String returnDate;

    @JsonSerialize(using = LocalDateTimeSerializer.class)
    @JsonDeserialize(using = LocalDateTimeDeserializer.class)
    @JsonFormat(shape = JsonFormat.Shape.STRING)
    private LocalDateTime returnTimestamp;

    // samo za *_FAILED
    private String reason;

    public BookVisibilitySagaEvent() {
    }

    public UUID getSagaId() {
        return sagaId;
    }

    public void setSagaId(UUID sagaId) {
        this.sagaId = sagaId;
    }

    public SagaEventType getEventType() {
        return eventType;
    }

    public void setEventType(SagaEventType eventType) {
        this.eventType = eventType;
    }

    public String getIsbn() {
        return isbn;
    }

    public void setIsbn(String isbn) {
        this.isbn = isbn;
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

    public LocalDateTime getLoanDate() {
        return loanDate;
    }

    public void setLoanDate(LocalDateTime loanDate) {
        this.loanDate = loanDate;
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

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }

    @Override
    public String toString() {
        return "BookVisibilitySagaEvent{" +
                "sagaId=" + sagaId +
                ", eventType=" + eventType +
                ", isbn='" + isbn + '\'' +
                ", bookId=" + bookId +
                ", loanId=" + loanId +
                ", memberId=" + memberId +
                ", reason='" + reason + '\'' +
                '}';
    }
}
