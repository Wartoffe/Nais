package rs.ac.uns.acs.Controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.Model.Author;
import rs.ac.uns.acs.Service.AuthorService;

import java.util.List;

@RestController
@RequestMapping("/authors")
public class AuthorController {

    private final AuthorService authorService;
    public AuthorController(AuthorService authorService){
        this.authorService=authorService;
    }
    @PostMapping
    public ResponseEntity<Author> create(@RequestBody Author author) {
        return ResponseEntity.status(HttpStatus.CREATED).body(authorService.create(author));
    }
    @GetMapping
    public ResponseEntity<List<Author>> findAll() {
        return ResponseEntity.ok(authorService.findAll());
    }
    @PutMapping("/{id}")
    public ResponseEntity<Author> update(@PathVariable Long id, @RequestBody Author author) {
        return ResponseEntity.ok(authorService.update(id, author));
    }
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        authorService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
