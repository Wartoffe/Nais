package com.library.requestservice.repository;

import com.library.requestservice.model.BorrowRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.Set;

@Repository
public class BorrowRequestRepository {

    private final RedisTemplate<String, BorrowRequest> redisTemplate;
    private final String keyPrefix;

    public BorrowRequestRepository(
            RedisTemplate<String, BorrowRequest> redisTemplate,
            @Value("${app.redis.request-prefix}") String keyPrefix) {
        this.redisTemplate = redisTemplate;
        this.keyPrefix = keyPrefix;
    }

    public BorrowRequest save(BorrowRequest request) {
        String key = buildKey(request.getId());
        redisTemplate.opsForValue().set(key, request);
        return request;
    }

    public Optional<BorrowRequest> findById(String id) {
        String key = buildKey(id);
        BorrowRequest request = redisTemplate.opsForValue().get(key);
        return Optional.ofNullable(request);
    }


    public List<BorrowRequest> findAll() {
        Set<String> keys = redisTemplate.keys(keyPrefix + "*");
        if (keys == null || keys.isEmpty()) {
            return List.of();
        }
        List<BorrowRequest> results = redisTemplate.opsForValue().multiGet(keys);
        return results == null ? List.of() : results.stream().filter(r -> r != null).toList();
    }

    public boolean deleteById(String id) {
        String key = buildKey(id);
        Boolean deleted = redisTemplate.delete(key);
        return Boolean.TRUE.equals(deleted);
    }

    public boolean existsById(String id) {
        String key = buildKey(id);
        return Boolean.TRUE.equals(redisTemplate.hasKey(key));
    }

    private String buildKey(String id) {
        return keyPrefix + id;
    }
}
