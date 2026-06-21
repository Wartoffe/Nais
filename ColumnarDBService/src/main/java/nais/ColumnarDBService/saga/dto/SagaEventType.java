package nais.ColumnarDBService.saga.dto;

/*
   Logika funkcionisanja:

   LoanService.createLoan spusti availableCopies na 0
       -> salje se HIDE_REQUESTED da bi elastic sakrio knjigu iz pretrage
   LoanService.returnBook poveca availableCopies sa 0
       -> salje se UNHIDE_REQUESTED da bi elastic vratio knjigu u pretragu
   Elastic prihvata *_REQUESTED i salje nazad *_COMPLETED ako je uspesno ili *_FAILED ako je nauspesno
   Ovaj servis ceka *_FAILED i rollbackuje prethodni deo
 */
public enum SagaEventType {
    HIDE_REQUESTED,
    HIDE_COMPLETED,
    HIDE_FAILED,
    UNHIDE_REQUESTED,
    UNHIDE_COMPLETED,
    UNHIDE_FAILED
}
