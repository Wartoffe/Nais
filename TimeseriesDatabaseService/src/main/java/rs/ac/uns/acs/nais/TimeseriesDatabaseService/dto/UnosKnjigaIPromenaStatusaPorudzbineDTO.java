package rs.ac.uns.acs.nais.TimeseriesDatabaseService.dto;

import rs.ac.uns.acs.nais.TimeseriesDatabaseService.model.PromenaStatusaPorudzbine;

import java.util.List;

public class UnosKnjigaIPromenaStatusaPorudzbineDTO {
    private PromenaStatusaPorudzbine promenaStatusaPorudzbine;
    private List<KnjigaDTO> knjige;

    public UnosKnjigaIPromenaStatusaPorudzbineDTO(PromenaStatusaPorudzbine promenaStatusaPorudzbine, List<KnjigaDTO> knjige) {
        this.promenaStatusaPorudzbine = promenaStatusaPorudzbine;
        this.knjige = knjige;
    }

    public PromenaStatusaPorudzbine getPromenaStatusaPorudzbine() {
        return promenaStatusaPorudzbine;
    }

    public void setPromenaStatusaPorudzbine(PromenaStatusaPorudzbine promenaStatusaPorudzbine) {
        this.promenaStatusaPorudzbine = promenaStatusaPorudzbine;
    }

    public List<KnjigaDTO> getKnjige() {
        return knjige;
    }

    public void setKnjige(List<KnjigaDTO> knjige) {
        this.knjige = knjige;
    }
}
