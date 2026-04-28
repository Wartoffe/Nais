package rs.ac.uns.acs.nais.GraphDatabaseService;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@SpringBootApplication
@EnableDiscoveryClient
public class GraphDatabaseServiceApplication {

	public static void main(String[] args) {
		SpringApplication.run(GraphDatabaseServiceApplication.class, args);
	}

}
