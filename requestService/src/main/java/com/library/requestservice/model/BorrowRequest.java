package com.library.requestservice.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.Instant;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class BorrowRequest implements Serializable {

    private String id;

    private String senderId;

    private String senderLibraryId;

    private String receiverLibraryId;

    private String respondedByLibrarianId;

    private String description;

    @Builder.Default
    private RequestStatus status = RequestStatus.PENDING;

    private Instant createdAt;
    private Instant updatedAt;
}
