package rs.ac.uns.acs.Service;

import jakarta.transaction.Transactional;
import org.springframework.stereotype.Service;
import rs.ac.uns.acs.Model.Author;
import rs.ac.uns.acs.Repository.AuthorRepository;

import java.util.List;

@Service
@Transactional
public class AuthorService {

    private final AuthorRepository authorRepository;
    public AuthorService(AuthorRepository authorRepository) {
        this.authorRepository = authorRepository;
    }

    public Author create(Author author){
        return authorRepository.save(author);
    }

    public List<Author> findAll() {
        return authorRepository.findAll();
    }
    public Author findById(Long id) {
        return authorRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Author not found with id: " + id));
    }
    public Author update(Long id, Author updated) {
        Author existing = findById(id);
        if(updated.getFirstName()!= null) {
            existing.setFirstName(updated.getFirstName());
        }
        if (updated.getLastName() != null) {
            existing.setLastName(updated.getLastName());
        }
        return authorRepository.save(existing);
    }
    public void delete(Long id) {
        Author author = findById(id);
        authorRepository.delete(author);
    }

}
