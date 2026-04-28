package rs.ac.uns.acs;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;


@SpringBootApplication(scanBasePackages = "rs.ac.uns.acs")
@EnableDiscoveryClient
public class RecommendationGraphServiceApplication {

	public static void main(String[] args) {
		SpringApplication.run(RecommendationGraphServiceApplication.class, args);
	}

}
