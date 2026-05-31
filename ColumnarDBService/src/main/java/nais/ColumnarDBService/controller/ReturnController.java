package nais.ColumnarDBService.controller;

import nais.ColumnarDBService.dto.ReturnDTO;
import nais.ColumnarDBService.service.ReturnService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/returns")
public class ReturnController {

    @Autowired
    private ReturnService returnService;

    @GetMapping
    public ResponseEntity<List<ReturnDTO>> getReturnsByDate(@RequestParam String date) {
        return ResponseEntity.ok(returnService.getReturnsByDate(date));
    }

    @GetMapping("/today")
    public ResponseEntity<List<ReturnDTO>> getReturnsForToday() {
        return ResponseEntity.ok(returnService.getReturnsForToday());
    }
    @GetMapping("/count")
    public ResponseEntity<Long> countReturnsByDate(@RequestParam String date) {
        return ResponseEntity.ok(returnService.countReturnsByDate(date));
    }
    @GetMapping("/today/count")
    public ResponseEntity<Long> countReturnsForToday() {
        return ResponseEntity.ok(returnService.countReturnsForToday());
    }
}
