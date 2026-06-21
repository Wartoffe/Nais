package rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography;

import java.util.Map;

// Koristim jer se ne podudaraju nazivi zanrova u timeSeries i bookAndReviewsService.
// Ova klasa normalizuje nazive zanrova.
public class ZanrNormalizer {
    private static final Map<String, String> MAPA = Map.ofEntries(
            Map.entry("FICTION", "FIKCIJA"),
            Map.entry("ROMANCE", "LJUBAVNI_ROMANI"),
            Map.entry("THRILLER", "TRILER"),
            Map.entry("MYSTERY", "MISTERIJA"),
            Map.entry("FANTASY", "FANTASTIKA"),
            Map.entry("HORROR", "HOROR"),
            Map.entry("YOUNG ADULT", "TINEJDZ"),
            Map.entry("HISTORICAL FICTION", "ISTORIJSKA_FIKCIJA"),
            Map.entry("NONFICTION", "NEFIKCIJA"),
            Map.entry("BIOGRAPHY", "BIOGRAFIJA"),
            Map.entry("POETRY", "POEZIJA"),
            Map.entry("CLASSICS", "KLASICI"),
            Map.entry("SCIENCE FICTION", "NAUCNA_FANTASTIKA"),
            Map.entry("HISTORY", "ISTORIJA"),
            Map.entry("PARANORMAL", "PARANORMALNO"),
            Map.entry("MANGA", "MANGA"),
            Map.entry("CHILDRENS", "DECIJE_KNJIGE"),
            Map.entry("PHILOSOPHY", "FILOZOFIJA"),
            Map.entry("COMICS", "STRIPOVI"),
            Map.entry("URBAN FANTASY", "URBANA_FANTASTIKA"),
            Map.entry("SHORT STORIES", "KRATKE_PRICE"),
            Map.entry("GRAPHIC NOVELS", "GRAFICKI_ROMANI")
    );

    private ZanrNormalizer() {
    }

    public static String normalizuj(String sirovZanr) {
        if (sirovZanr == null || sirovZanr.isBlank()) {
            return "NEPOZNATO";
        }
        String kljuc = sirovZanr.trim().toUpperCase();
        return MAPA.getOrDefault(kljuc, kljuc.replace(" ", "_"));
    }
}
