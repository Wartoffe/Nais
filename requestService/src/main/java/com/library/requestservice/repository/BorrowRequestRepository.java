package com.library.requestservice.repository;
import com.library.requestservice.model.BorrowRequest;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
@Repository
public interface BorrowRequestRepository extends JpaRepository<BorrowRequest, String> {
}
