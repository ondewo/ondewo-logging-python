<p align="center">
    <a href="https://www.ondewo.com">
      <img alt="ONDEWO Logo" src="https://raw.githubusercontent.com/ondewo/ondewo-logos/master/github/ondewo_logo_github_2.png"/>
    </a>
  <h1 align="center">
    ONDEWO Logging
  </h1>
</p>


This is the logging package for ONDEWO products. It allows for easy integration with our EFK stack, and adds some useful features to the base python logging package (such as timing and exception handling), and handles GRPC error messages nicely.

## Useage

To use this library, first pip install it:
```
pip install ondewo-logging
```

then import it into your project like so:
```
from ondewo.logging.logger import logger_console
```

## Decorators

A couple of decorators are included:
```
from ondewo.logging.decorators import Timer, timing, exception_handling, exception_silencing
```

The Timer class can be used as a context manager:
```
with Timer() as t:
  sleep(1)
```

or as a decorator:
```
@Timer()
def sleeptime():
  sleep(1)
```
and can be used with different messages or logging levels:
* Logging level: `@Timer(logger=logger_console.info)`
* Message: `@Timer(message="MESSAGE WITH TIME {} {}")`, `@Timer(message="SIMPLER MESSAGE WITHOUT TIME")`
* Disable argument logging: `@Timer(log_arguments=False)`
* Enable exception suppression: `@Timer(supress_exceptions=True)`

See the tests for detailed examples of how these work.

Timing is just an instance of the Timer class:
```
timing = Timer()
```
for backwards compatibility.

The exception_handling function is a decorator which will log errors nicely using the ondewo logging syntax (below). It will also log the inputs and outputs of the function. The exception_silencing function just shows the inputs and outputs and gets rid of the stacktrace, it can be useful for debugging. Finally, log_arguments will dump the inputs and outputs of a function into the logs.


# Ondewo log format

The structure of the logs looks like this:
```
message: Dict[str, Any] = {
  "message": f"Here is the normal log, including relevant information such the magic number: {magic number}. These values are also added seperately below, either just with the variable name or some other relevant name. Finally, there are some tags to help with searching through the logs.",
  "magic_number": magic_number,
  "tags": ["magic", "number"]
}
```

# Note on tags:

The tags allow for easy searching and grouping in kibana. They can be added in a somewhat ad-hoc manner by the programmer on the ground, though some (like 'timing') are standardised. Please talk to your project team lead for details.

# Fluentd

## Quickstart

1) git clone https://github.com/ondewo/ondewo-logging-python
2) make
3) edit the fluentd config with the url and password of your elasticsearch host:
```
sed -i 's/<PASSWORD>/my_password/' './fluentd/conf/fluent.conf'
sed -i 's/<HOST>/my_elasticsearch_host/' './fluentd/conf/fluent.conf'
```
4) run fluentd `docker-compose -f fluentd/docker-compose.yaml up -d`

You now have a fluentd message handler running on your machine. If you use the ondewo.logging library, your logs will be shipped to your elasticsearch server.

## Fluentd Config

Per the `fluentd/docker-compose.yaml`, we map the configuration files and the logs into the fluentd image and open some ports. **We also need to `chown -R 100:"$GID" fluentd/log`**. That command should allow both you and fluentd to read the logs.

Beyond that, it is just a question of formatting the logs wherever they come from. Here is the example from the fluentd config that sends stuff to the fluentd stdout, so you can see the logs from all your images in the same place.
```
<source>
  @type forward
  port 24224
</source>

# py.console logging gets piped to stdout
<match py.console.**>
  @type stdout
  <format>
      @type ltsv
      delimiter_pattern :
      label_delimiter =
  </format>
</match>

```

In this conf, we recieve imput over a tcp connection, then dumps the output to stdout, so you can use that stream to watch log output via fluentd. The config is also set up to save all the logs locally, and ship them to a remote server.
