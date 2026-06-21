package nais.search.exception;

/**
 * Thrown when a book cannot be located (by recordId or by ISBN) for a
 * read, hide, or unhide operation. Used by the saga listener to decide
 * that a hide/unhide request has failed and must be reported back to
 * ColumnarDBService so it can roll back its local transaction.
 */
public class BookNotFoundException extends RuntimeException {

    public BookNotFoundException(String message) {
        super(message);
    }
}
