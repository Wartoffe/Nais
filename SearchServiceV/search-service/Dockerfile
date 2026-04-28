FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o search-service .

FROM alpine:3.20
WORKDIR /app
COPY --from=builder /app/search-service /app/search-service
EXPOSE 8080
CMD ["/app/search-service"]
