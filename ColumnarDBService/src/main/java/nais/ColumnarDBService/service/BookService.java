package nais.ColumnarDBService.service;

import nais.ColumnarDBService.dto.BookDTO;
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



}
