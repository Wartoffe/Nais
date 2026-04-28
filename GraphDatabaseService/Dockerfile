# -------------------------------------------------------
# buildovanje projekta
FROM maven:3.9.6-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests


# -------------------------------------------------------
# pokretanje aplikacije
FROM eclipse-temurin:21-jre AS final
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 9050
ENTRYPOINT ["java", "-jar", "app.jar"]