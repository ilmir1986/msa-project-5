FROM eclipse-temurin:25
# 8080
WORKDIR .
COPY build/libs/batch-processing-0.0.1-SNAPSHOT.jar app.jar
ENTRYPOINT ["java","-jar","/app.jar"]