package nais.search.service;

import nais.search.dto.BookDto;
import nais.search.model.Book;
import nais.search.repository.BookRepository;
import org.springframework.data.domain.Page;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class BookService {

    private final BookRepository bookRepository;

    public BookService(BookRepository bookRepository) {
        this.bookRepository = bookRepository;
    }

    public Optional<Book> getBookByRecordId(String recordId){
        return bookRepository.findByRecordId(recordId);
    }

    public Book createNewBook(Book book){
        return bookRepository.save(book);
    }

    public Book updateBook(String recordId, BookDto dto) {
        Optional<Book> existing = bookRepository.findByRecordId(recordId);
        if (existing.isEmpty()) return null;

        Book book = existing.get();

        if (dto.getIsbns()         != null) book.setIsbns(dto.getIsbns());
        if (dto.getTitle()         != null) book.setTitle(dto.getTitle());
        if (dto.getOriginalTitle() != null) book.setOriginalTitle(dto.getOriginalTitle());
        if (dto.getSubtitle()      != null) book.setSubtitle(dto.getSubtitle());
        if (dto.getAuthors()       != null) book.setAuthors(dto.getAuthors());
        if (dto.getGenres()        != null) book.setGenres(dto.getGenres());
        if (dto.getLanguage()      != null) book.setLanguage(dto.getLanguage());
        if (dto.getTranslators()   != null) book.setTranslators(dto.getTranslators());
        if (dto.getIllustrators()  != null) book.setIllustrators(dto.getIllustrators());
        if (dto.getIntroductions() != null) book.setIntroductions(dto.getIntroductions());
        if (dto.getAfterwords()    != null) book.setAfterwords(dto.getAfterwords());
        if (dto.getPublisher()     != null) book.setPublisher(dto.getPublisher());
        if (dto.getPublishDate()   != null) book.setPublishDate(dto.getPublishDate());
        if (dto.getFormat()        != null) book.setFormat(dto.getFormat());
        if (dto.getSeries()        != null) book.setSeries(dto.getSeries());
        if (dto.getTextExcerpt()   != null) book.setTextExcerpt(dto.getTextExcerpt());
        if (dto.getDescription()   != null) book.setDescription(dto.getDescription());
        if (dto.getNumberOfPages() != null) book.setNumberOfPages(dto.getNumberOfPages());
        if (dto.getAwards()        != null) book.setAwards(dto.getAwards());
        if (dto.getSetting()       != null) book.setSetting(dto.getSetting());
        if (dto.getCharacters()    != null) book.setCharacters(dto.getCharacters());

        return bookRepository.save(book);
    }


    public boolean deleteBook(String recordId){
        bookRepository.deleteById(recordId);
        return true;
    }

    public Page<Book> fullTextSearch(){
        return null;
    }

    public Page<Book> filteredKeywordSearch(){
        return null;
    }
}
