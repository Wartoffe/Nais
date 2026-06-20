package nais.search.saga.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.annotation.JsonSerialize;
import com.fasterxml.jackson.datatype.jsr310.deser.LocalDateTimeDeserializer;
import com.fasterxml.jackson.datatype.jsr310.ser.LocalDateTimeSerializer;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * Saga event payload shared (by JSON shape, not by class) between
 * ColumnarDBService and the search service. Each service keeps its own
 * copy of this class in its own package; the RabbitMQ message converter
 * is configured on both sides to map the same logical type id
 * ("BookVisibilitySagaEvent") to each service's local copy, so the two
 * Maven modules never need to share a library.
 *
 * Field usage by event type:
 *  - HIDE_REQUESTED / UNHIDE_REQUESTED: isbn, bookId, bookTitle,
 *    bookGenre, loanId, memberId, loanDate are always set.
 *    returnDate / returnTimestamp are additionally set for
 *    UNHIDE_REQUESTED (needed to compensate a returnBook).
 *  - *_COMPLETED / *_FAILED: echoes the same correlation fields back;
 *    reason is set only for *_FAILED.
 */
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

    // Only populated for unhide (return) events, needed to delete the
    // ReturnByDate record if ColumnarDBService has to compensate.
    private String returnDate;

    @JsonSerialize(using = LocalDateTimeSerializer.class)
    @JsonDeserialize(using = LocalDateTimeDeserializer.class)
    @JsonFormat(shape = JsonFormat.Shape.STRING)
    private LocalDateTime returnTimestamp;

    // Populated only on *_FAILED events.
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
