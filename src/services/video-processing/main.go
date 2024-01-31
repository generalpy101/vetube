package main

import (
	"flag"
	"log"
	"os"
	"time"

	rabbitmq "src/services/internal/rabbitmq"

	amqp "github.com/rabbitmq/amqp091-go"
)

var (
	uri               = flag.String("uri", "amqp://guest:guest@localhost:5672/", "AMQP URI")
	exchange          = flag.String("exchange", "videos", "Durable, non-auto-deleted AMQP exchange name")
	exchangeType      = flag.String("exchange-type", "topic", "Exchange type - direct|fanout|topic|x-custom")
	queue             = flag.String("queue", "uploaded", "Ephemeral AMQP queue name")
	bindingKey        = flag.String("key", "video.uploaded", "AMQP binding key")
	consumerTag       = flag.String("consumer-tag", "simple-consumer", "AMQP consumer tag (should not be blank)")
	lifetime          = flag.Duration("lifetime", 0*time.Second, "lifetime of process before shutdown (0s=infinite)")
	verbose           = flag.Bool("verbose", true, "enable verbose output of message data")
	ErrLog            = log.New(os.Stderr, "[ERROR] ", log.LstdFlags|log.Lmsgprefix)
	Log               = log.New(os.Stdout, "[INFO] ", log.LstdFlags|log.Lmsgprefix)
	deliveryCount int = 0
)

func main() {
	flag.Parse()
	consumer, err := rabbitmq.NewConsumer(*uri, *exchange, *exchangeType, *queue, *bindingKey, *consumerTag, rabbitMQHandler)
	if err != nil {
		ErrLog.Fatalf("%s", err)
	}

	rabbitmq.SetupCloseHandler(consumer)

	if *lifetime > 0 {
		Log.Printf("running for %s", *lifetime)
		time.Sleep(*lifetime)
	} else {
		Log.Printf("running until Consumer is done")
		<-consumer.Done
	}

	Log.Printf("shutting down")

	if err := consumer.Shutdown(); err != nil {
		ErrLog.Fatalf("error during shutdown: %s", err)
	}
}

func rabbitMQHandler(deliveries <-chan amqp.Delivery, done chan error) error {
	Log.Printf("Received message")

	cleanup := func() {
		Log.Printf("Closing delivery channel")
		done <- nil
	}

	defer cleanup()

	// Print messages
	for d := range deliveries {
		deliveryCount++
		Log.Printf(
			"[%d] %s",
			deliveryCount,
			d.Body,
		)

	}

	return nil
}
