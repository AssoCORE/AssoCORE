# Stage 1: Build APK with minimal Flutter setup
FROM ghcr.io/cirruslabs/flutter:stable AS builder
WORKDIR /app

# Install OpenJDK 17 for Android builds
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Disable Flutter analytics
ENV FLUTTER_TELEMETRY_DISABLED=1
ENV PUB_CACHE=/root/.pub-cache

# Copy mobile app source
COPY mobile/ ./

# Accept Android licenses and get dependencies
RUN yes | flutter doctor --android-licenses || true && \
    flutter config --no-analytics && \
    flutter pub get

# Build APK for release
RUN flutter build apk --release

# Stage 2: Extract APK
FROM alpine:latest AS runner
WORKDIR /output

# Copy built APK from builder
COPY --from=builder /app/build/app/outputs/flutter-apk/app-release.apk ./assocore.apk

# Display APK info
RUN ls -lh /output/assocore.apk

# Keep container running to allow copying the APK
CMD ["sh", "-c", "echo 'APK built successfully at /output/assocore.apk' && tail -f /dev/null"]
