package rs.ac.uns.acs.Service;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.Model.Genre;
import rs.ac.uns.acs.Repository.AuthorRepository;
import rs.ac.uns.acs.Repository.GenreRepository;

import java.util.List;

@Service
public class GenreService {
    private final GenreRepository genreRepository;

    public GenreService(GenreRepository genreRepository) {
        this.genreRepository = genreRepository;
    }

    public Genre create(Genre genre) {
        if (genreRepository.existsByName(genre.getName())) {
            throw new RuntimeException("Genre already exists: " + genre.getName());
        }
        return genreRepository.save(genre);
    }

    public List<Genre> findAll() {
        return genreRepository.findAll();
    }
    public Genre findById(Long id) {
        return genreRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Genre not found with id: " + id));
    }
    public Genre update(Long id, Genre updated) {
        Genre existing = findById(id);
        existing.setName(updated.getName());
        return genreRepository.save(existing);
    }
    public void delete(Long id) {
        Genre genre = findById(id);
        genreRepository.delete(genre);
    }
}
