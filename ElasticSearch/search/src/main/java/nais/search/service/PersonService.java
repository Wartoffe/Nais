package nais.search.service;

import nais.search.dto.PersonDto;
import nais.search.model.Person;
import nais.search.repository.PersonRepository;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class PersonService {

    private final PersonRepository personRepository;

    public PersonService(PersonRepository personRepository) {
        this.personRepository = personRepository;
    }

    public Optional<Person> getPersonById(String personId) {
        return personRepository.findById(personId);
    }

    public Person createNewPerson(Person person) {
        return personRepository.save(person);
    }

    public boolean deletePerson(String personId) {
        personRepository.deleteById(personId);
        return true;
    }

    public Person updatePerson(String personId, PersonDto dto) {
        Optional<Person> existing = personRepository.findById(personId);
        if (existing.isEmpty()) return null;

        Person person = existing.get();

        if (dto.getFirstName()    != null) person.setFirstName(dto.getFirstName());
        if (dto.getLastName()     != null) person.setLastName(dto.getLastName());
        if (dto.getPlaceOfBirth() != null) person.setPlaceOfBirth(dto.getPlaceOfBirth());
        if (dto.getDateOfBirth()  != null) person.setDateOfBirth(dto.getDateOfBirth());
        if (dto.getDateOfDeath()  != null) person.setDateOfDeath(dto.getDateOfDeath());
        if (dto.getRole()         != null) person.setRole(dto.getRole());
        if (dto.getGenres()       != null) person.setGenres(dto.getGenres());
        if (dto.getBooks()        != null) person.setBooks(dto.getBooks());
        if (dto.getBio()          != null) person.setBio(dto.getBio());

        return personRepository.save(person);
    }
}