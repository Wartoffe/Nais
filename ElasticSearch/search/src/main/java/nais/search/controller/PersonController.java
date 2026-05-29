package nais.search.controller;

import nais.search.model.Person;
import nais.search.service.PersonService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Optional;

@RestController
@RequestMapping("/api/person")
public class PersonController {

    private final PersonService personService;

    public PersonController(PersonService personService) {
        this.personService = personService;
    }

    @GetMapping("/{personId}")
    public Optional<Person> getPersonById(){}

    @PostMapping("/create")
    public ResponseEntity<?> newPerson(){}

    @PatchMapping("/{personId}")
    public ResponseEntity<?> updatePerson(){}

    @DeleteMapping("/{personId}")
    public ResponseEntity<?> deletePerson(){}
}
