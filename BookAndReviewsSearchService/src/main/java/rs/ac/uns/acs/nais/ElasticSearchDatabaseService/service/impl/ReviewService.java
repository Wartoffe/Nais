package rs.ac.uns.acs.nais.ElasticSearchDatabaseService.service.impl;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.nais.ElasticSearchDatabaseService.model.Review;
import rs.ac.uns.acs.nais.ElasticSearchDatabaseService.repository.ReviewRepository;
import rs.ac.uns.acs.nais.ElasticSearchDatabaseService.service.IReviewService;

import java.util.List;
import java.util.Optional;
import java.util.stream.StreamSupport;

/**
 * Service layer for review search and management backed by Elasticsearch.
 * Delegates all Elasticsearch interactions to ReviewRepository, which uses
 * Spring Data Elasticsearch and custom @Query annotations to build various
 * search strategies.
 */
@Service
public class ReviewService implements IReviewService {
    private final ReviewRepository reviewRepository;

    public ReviewService(ReviewRepository reviewRepository) {
        this.reviewRepository = reviewRepository;
    }

    // CREATE
    @Override
    public Review save(Review review) {
        return reviewRepository.save(review);
    }

    @Override
    public List<Review> saveAll(List<Review> reviews) {
        Iterable<Review> saved = reviewRepository.saveAll(reviews);
        return StreamSupport.stream(saved.spliterator(), false).toList();
    }

    // UPDATE
    @Override
    public Review update(String id, Review review) {
        if (!reviewRepository.existsById(id)) {
            throw new IllegalArgumentException("Review with ID '" + id + "' does not exist in index.");
        }
        review.setReviewId(id);
        return reviewRepository.save(review);
    }

    // DELETE
    @Override
    public void deleteById(String id) {
        reviewRepository.deleteById(id);
    }

    @Override
    public void deleteAllById(List<String> ids) {
        reviewRepository.deleteAllById(ids);
    }

    // READ
    @Override
    public Optional<Review> findById(String id) {
        return reviewRepository.findById(id);
    }

    @Override
    public List<Review> findAll() {
        Iterable<Review> all = reviewRepository.findAll();
        return StreamSupport.stream(all.spliterator(), false).toList();
    }

    @Override
    public List<Review> findAllById(List<String> ids) {
        Iterable<Review> found = reviewRepository.findAllById(ids);
        return StreamSupport.stream(found.spliterator(), false).toList();
    }
}
