package nais.ColumnarDBService.saga.dto;

/**
 * The set of events exchanged on the "library.saga.exchange" topic
 * exchange between ColumnarDBService and the Elasticsearch search
 * service, as part of the choreography saga that keeps book
 * availability (Cassandra) and book visibility (Elasticsearch) in
 * sync.
 *
 * Flow:
 *  - LoanService.createLoan drops availableCopies to 0
 *      -> publishes HIDE_REQUESTED
 *  - LoanService.returnBook raises availableCopies from 0
 *      -> publishes UNHIDE_REQUESTED
 *  - The search service consumes *_REQUESTED, performs the logical
 *    delete/undelete locally, and publishes back *_COMPLETED on
 *    success or *_FAILED on failure.
 *  - This service consumes *_FAILED and compensates (rolls back) the
 *    original createLoan/returnBook transaction.
 */
public enum SagaEventType {
    HIDE_REQUESTED,
    HIDE_COMPLETED,
    HIDE_FAILED,
    UNHIDE_REQUESTED,
    UNHIDE_COMPLETED,
    UNHIDE_FAILED
}
