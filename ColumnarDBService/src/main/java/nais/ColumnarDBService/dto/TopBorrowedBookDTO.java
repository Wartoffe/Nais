package nais.ColumnarDBService.dto;

import java.util.UUID;

public class TopBorrowedBookDTO {

    private UUID bookId;
    private String title;
    private String genre;
    private String author;
    private long totalLoans;
    private int availableCopies;
    private int totalCopies;

    public TopBorrowedBookDTO() {
    }

    public TopBorrowedBookDTO(UUID bookId, String title, String genre, String author, long totalLoans, int availableCopies, int totalCopies) {
        this.bookId = bookId;
        this.title = title;
        this.genre = genre;
        this.author = author;
        this.totalLoans = totalLoans;
        this.availableCopies = availableCopies;
        this.totalCopies = totalCopies;
    }

    public UUID getBookId() {
        return bookId;
    }

    public void setBookId(UUID bookId) {
        this.bookId = bookId;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getGenre() {
        return genre;
    }

    public void setGenre(String genre) {
        this.genre = genre;
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public long getTotalLoans() {
        return totalLoans;
    }

    public void setTotalLoans(long totalLoans) {
        this.totalLoans = totalLoans;
    }

    public int getAvailableCopies() {
        return availableCopies;
    }

    public void setAvailableCopies(int availableCopies) {
        this.availableCopies = availableCopies;
    }

    public int getTotalCopies() {
        return totalCopies;
    }

    public void setTotalCopies(int totalCopies) {
        this.totalCopies = totalCopies;
    }
}
