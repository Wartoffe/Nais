package nais.ColumnarDBService.service;

import nais.ColumnarDBService.dto.ReturnDTO;
import nais.ColumnarDBService.mapper.LibraryMapper;
import nais.ColumnarDBService.repository.ReturnByDateRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class ReturnService {

    @Autowired
    private ReturnByDateRepository returnByDateRepository;

    @Autowired
    private LibraryMapper mapper;
    public List<ReturnDTO> getReturnsByDate(String date) {
        return returnByDateRepository.findByReturnDate(date)
                .stream()
                .map(mapper::returnByDateToReturnDTO)
                .collect(Collectors.toList());
    }

    public List<ReturnDTO> getReturnsForToday() {
        String today = LocalDate.now().toString();
        return returnByDateRepository.findByReturnDate(today)
                .stream()
                .map(mapper::returnByDateToReturnDTO)
                .collect(Collectors.toList());
    }
    public Long countReturnsByDate(String date) {
        return returnByDateRepository.countByReturnDate(date);
    }
    public Long countReturnsForToday() {
        return returnByDateRepository.countByReturnDate(LocalDate.now().toString());
    }



}
