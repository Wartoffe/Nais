package rs.ac.uns.acs.nais.TimeseriesDatabaseService.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class KnjigaDTO {
    @NotNull
    @Min(1)
    private Integer goodreads_id;

    @NotBlank
    @Size(max = 32)
    private String isbn;

    @NotBlank
    @Size(max = 512)
    private String title;

    @NotBlank
    @Size(max = 256)
    private String author;

    @NotBlank
    @Size(max = 6000)
    private String description;

    @Size(min = 2, max = 32)
    private String language;

    @Size(max = 256)
    private String publisher;

    @Min(0)
    @Max(100_000)
    private Integer pages;

    @Size(max = 2048)
    private String coverImg;

    private Boolean has_image;

    public KnjigaDTO() {
    }

    public KnjigaDTO(Integer goodreads_id, String isbn, String title, String author, String description, String language, String publisher, Integer pages, String coverImg, Boolean has_image) {
        this.goodreads_id = goodreads_id;
        this.isbn = isbn;
        this.title = title;
        this.author = author;
        this.description = description;
        this.language = (language == null || language.isBlank()) ? "en" : language.trim();
        this.publisher = (publisher == null) ? "" : publisher.trim();
        this.pages = (pages == null) ? 0 : pages;
        setCoverImg(coverImg);
    }

    public Integer getGoodreads_id() {
        return goodreads_id;
    }

    public void setGoodreads_id(Integer goodreads_id) {
        this.goodreads_id = goodreads_id;
    }

    public String getIsbn() {
        return isbn;
    }

    public void setIsbn(String isbn) {
        this.isbn = isbn;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getLanguage() {
        return language;
    }

    public void setLanguage(String language) {
        this.language = language;
    }

    public String getPublisher() {
        return publisher;
    }

    public void setPublisher(String publisher) {
        this.publisher = publisher;
    }

    public Integer getPages() {
        return pages;
    }

    public void setPages(Integer pages) {
        this.pages = pages;
    }

    public String getCoverImg() {
        return coverImg;
    }

    public void setCoverImg(String coverImg) {
        this.coverImg = (coverImg == null || coverImg.isBlank()) ? null : coverImg.trim();
        this.has_image = this.coverImg != null;
    }

    public Boolean getHas_image() {
        return has_image;
    }

    public void setHas_image(Boolean has_image) {
        this.has_image = has_image != null && has_image;
    }
}
