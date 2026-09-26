FROM eclipse-temurin:21-jre
WORKDIR /app
COPY target/gateway.jar jvm.options ./
# The container runs with a 2 GiB memory limit and 2 CPUs.
CMD ["java", "@jvm.options", "-jar", "gateway.jar"]
