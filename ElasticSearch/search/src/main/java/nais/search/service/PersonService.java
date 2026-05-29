package nais.search.service;

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

    public Optional<Person> getPersonById(String personId){
        return personRepository.findByPersonId(personId);
    }

    public Person createNewPerson(Person person){
        return personRepository.save(person);
    }

    public boolean deletePerson(String personId){
        personRepository.deleteById(personId);
        return true;
    }

    public Person updatePerson(String personId, Person person){
        Person targetPerson = personRepository.findByPersonId(personId).get();
        targetPerson = person;
        return personRepository.save(targetPerson);
    }


}
