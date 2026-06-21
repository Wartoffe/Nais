package rs.ac.uns.acs.nais.TimeseriesDatabaseService.configuration;

import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Configuration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.cache.RedisCacheManager;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext;

import java.time.Duration;

@EnableCaching
@Configuration
public class RedisConfig {

    @Value("${spring.data.redis.host}")
    private String redisHost;

    @Value("${spring.data.redis.port}")
    private int redisPort;

    /**
     * Kreira fabriku konekcija koristeći Lettuce drajver.
     * Konfigurisana je za "Standalone" režim, što znači da radi sa jednim Redis nodom (nije klaster/sentinel).
     */
    @Bean
    public LettuceConnectionFactory redisConnectionFactory() {
        RedisStandaloneConfiguration configuration = new RedisStandaloneConfiguration(redisHost, redisPort);
        return new LettuceConnectionFactory(configuration);
    }


    @Bean
    public RedisCacheManager cacheManager() {
        /**
         * 1. Default konfiguracija za sve keševe koji nisu eksplicitno imenovani:
         * - TTL je postavljen na 10 minuta.
         * - disableCachingNullValues() sprečava da se 'null' rezultati upišu u keš
         *   (Korisno da se ne bi keširao nepostojeći entitet ako baza vrati null)
         */
        RedisCacheConfiguration defaultConfig = myDefaultCacheConfig(Duration.ofMinutes(10)).disableCachingNullValues();

        /**
         * 2. Izgradnja RedisCacheManager-a:
         * - Povezuje se na definisanu fabriku konekcija (redisConnectionFactory()).
         * - Postavlja default pravila (10 min TTL, bez null vrednosti)
         * - .withCacheConfiguration("orders", ...) kreira poseban prostor pod nazivom "orders"
         *   Za njega važi kraći TTL od 5 minuta, ali pošto se ovde ponovo poziva
         *   myDefaultCacheConfig() bez .disableCachingNullValues(), u "orders" kešu ĆE SE keširati null vrednosti
         */
        return RedisCacheManager.builder(redisConnectionFactory())
                .cacheDefaults(defaultConfig)
                .withCacheConfiguration("orders", myDefaultCacheConfig(Duration.ofMinutes(5)))
                .build();
    }

    /**
     * Pomoćna privatna metoda koja generiše bazičnu konfiguraciju za keš
     *
     * @param duration Vreme trajanja keša (TTL) nakon kog podatak ističe iz Redis-a
     */
    private RedisCacheConfiguration myDefaultCacheConfig(Duration duration) {
        return RedisCacheConfiguration
                .defaultCacheConfig()
                .entryTtl(duration)
                /**
                 * Serijalizacija vrednosti u JSON format pomoću Jackson biblioteke
                 * Ključevi ostaju u podrazumevanom String formatu, dok se objekti pretvaraju u čitljiv JSON
                 * Prednost: Može se direktno u Redis-u (preko Redis Insight-a) videto šta je keširano
                 * Mana: Zahteva da objekti imaju prazne konstruktore i getere/setere za ispravnu deserijalizaciju
                 */
                .serializeValuesWith(RedisSerializationContext.SerializationPair.fromSerializer(new GenericJackson2JsonRedisSerializer()));
    }
}