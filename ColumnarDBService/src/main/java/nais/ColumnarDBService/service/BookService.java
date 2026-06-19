package nais.ColumnarDBService.service;

import nais.ColumnarDBService.dto.BookDTO;
import nais.ColumnarDBService.entity.BookByGenre;
import nais.ColumnarDBService.mapper.LibraryMapper;
import nais.ColumnarDBService.repository.BookByGenreRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class BookService {

    @Autowired
    private BookByGenreRepository bookByGenreRepository;
    @Autowired
    private LibraryMapper mapper;

    //kreiranje knjiga
    public BookDTO createBook(BookDTO dto){
        if(dto.getBookId()==null){
            dto.setBookId(UUID.randomUUID());
        }
        bookByGenreRepository.save(mapper.bookDTOToBookByGenre(dto));
        return dto;
    }

    //sve knjige datog zanra
    public List<BookDTO> getBooksByGenre(String genre) {
        return bookByGenreRepository.findByGenre(genre)
                .stream()
                .map(mapper::bookByGenreToBookDTO)
                .collect(Collectors.toList());
    }

    //broj knjiga po zanru
    public Long countBooksByGenre(String genre) {
        return bookByGenreRepository.countByGenre(genre);
    }

    public BookDTO updateBook(BookDTO dto) {
        bookByGenreRepository.save(mapper.bookDTOToBookByGenre(dto));
        return dto;
    }
    public void deleteBook(String genre, String title, UUID bookId) {
        bookByGenreRepository.deleteBook(genre, title, bookId);
    }
    public BookDTO decreaseAvailableCopies(String genre, String title, UUID bookId){
        BookByGenre book= bookByGenreRepository.findByGenreAndTitleAndBookId(genre, title,bookId);
        if (book==null) throw new RuntimeException("Knjiga nije pronadjena");

        if(book.getAvailableCopies()<=0){
            throw new RuntimeException("Nema dostupnih primeraka knjige");
        }
        book.setAvailableCopies(book.getAvailableCopies()-1);
        bookByGenreRepository.save(book);
        return mapper.bookByGenreToBookDTO(book);
    }

    public BookDTO increaseAvailableCopies (String genre, String title, UUID bookId){
        BookByGenre book= bookByGenreRepository.findByGenreAndTitleAndBookId(genre, title, bookId);
        if (book==null) throw new RuntimeException("Knjiga nije pronadjena");
        if(book.getAvailableCopies()<book.getTotalCopies()){
            book.setAvailableCopies(book.getAvailableCopies()+1);
            bookByGenreRepository.save(book);
        }
        return  mapper.bookByGenreToBookDTO(book);

    }



}
