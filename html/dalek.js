import { Spinner } from "./spin.js";

$(document).ready(function () {
  var READY = "ready";
  var BUSY = "busy";
  var EXIT = "exit";
  var BEGIN = "begin";
  var RELEASE = "release";
  var DRIVE = "drive";
  var TURN = "turn";
  var STOP = "stop";
  var HEAD_TURN = "headturn";
  var PLAY_SOUND = "playsound";
  var STOP_SOUND = "stopsound";
  var SNAPSHOT = "snapshot";
  var TOGGLE_LIGHTS = "togglelights";
  var BATTERY = "battery";

  function Socket(callbacks) {
    var STATE_DISCONNECTED = 0;
    var STATE_READY = 1;
    var STATE_BUSY = 2;

    var verbose = false;
    var state = STATE_DISCONNECTED;
    var socket = null;

    function log(arg) {
      if (verbose) {
        console.log(arg);
      }
    }

    function logError(args) {
      console.log("Network: bad message '%s'", args);
    }

    function onmessage(event) {
      log(event);
      if (typeof event.data === "string") {
        var msg = JSON.parse(event.data.trim());
        log(msg);

        if (Array.isArray(msg) && msg.length > 0) {
          var cmd = msg[0];
          var args = msg.slice(1);

          if (cmd === READY && state !== STATE_READY && args.length > 0) {
            state = STATE_READY;
            callbacks.ready();
            callbacks.battery(args[0]);
          } else if (cmd === BUSY) {
            if (state != STATE_BUSY) {
              callbacks.busy();
            }
            state = STATE_BUSY;
            socket.close();
          } else if (
            cmd === BATTERY &&
            state === STATE_READY &&
            args.length > 0
          ) {
            callbacks.battery(args[0]);
          } else if (
            cmd === SNAPSHOT &&
            state === STATE_READY &&
            args.length > 0
          ) {
            callbacks.snapshot(args[0]);
          } else {
            logError(msg);
          }
        } else {
          logError(event.data);
        }
      } else {
        logError(event.data);
      }
    }

    function onclose(event) {
      log(event);
      if (state === STATE_READY) {
        callbacks.disconnected();
        state = STATE_DISCONNECTED;
      }
      if (socket !== null) {
        socket = null;
        window.setTimeout(connectionAttempt, 5000);
      }
    }

    function onerror(event) {
      log(event);
      if (state !== STATE_DISCONNECTED) {
        callbacks.disconnected();
        state = STATE_DISCONNECTED;
      }
      if (socket !== null) {
        socket = null;
        window.setTimeout(connectionAttempt, 5000);
      }
    }

    function connectionAttempt() {
      if (state === STATE_DISCONNECTED || state === STATE_BUSY) {
        socket = new WebSocket("ws://" + window.location.hostname + ":12346");
        socket.onmessage = onmessage;
        socket.onclose = onclose;
        socket.onerror = onerror;
      }
    }

    function send() {
      if (state === STATE_READY) {
        var data = JSON.stringify(Array.from(arguments));
        if (verbose) {
          console.log("Network sending: '%s'", data);
        }
        socket.send(data + "\n");
      }
    }

    connectionAttempt();

    return {
      toggleVerbose: function () {
        verbose = !verbose;
      },
      beginCmd: function (cmd, value) {
        send(BEGIN, cmd, value);
      },
      releaseCmd: function (cmd, value) {
        send(RELEASE, cmd, value);
      },
      stop: function () {
        send(STOP);
      },
      playSound: function (sound) {
        send(PLAY_SOUND, sound);
      },
      stopSound: function () {
        send(STOP_SOUND);
      },
      snapshot: function () {
        send(SNAPSHOT);
      },
      toggleLights: function () {
        send(TOGGLE_LIGHTS);
      },
      exit: function () {
        send(EXIT);
        socket.close();
      },
    };
  }

  function Timer(fn, interval) {
    var timer = null;

    function stop() {
      if (timer !== null) {
        window.clearTimeout(timer);
      }
      timer = null;
    }

    return {
      restart: function () {
        stop();
        timer = window.setTimeout(fn, interval);
      },
      stop: stop,
    };
  }

  function RateLimit(msec, callback) {
    var last_called = 0;

    function timeSince(time) {
      return new Date().getTime() - time;
    }

    return {
      call: function () {
        if (timeSince(last_called) > msec) {
          last_called = new Date().getTime();
          callback.apply(null, arguments);
        }
      },
      reset: function () {
        last_called = 0;
      },
    };
  }

  function SpinnerWidget(parent_id) {
    var parent = $(parent_id)[0];
    var spinner = new Spinner({
      color: "#3d86cb",
      lines: 13,
      radius: 40,
      length: 50,
      width: 14,
      corners: 1,
    });

    return {
      start: function () {
        spinner.spin(parent);
      },
      stop: function () {
        spinner.stop();
      },
    };
  }

  function DialogBox(trigger_id, box_id, close_button_id) {
    var modal = $(box_id);
    var close = $(close_button_id);

    modal.modal({
      backdrop: "static",
      keyboard: false,
      show: false,
    });

    $(trigger_id).click(function () {
      modal.modal("show");
    });

    close.click(function () {
      modal.modal("hide");
    });
  }

  function DisconnectedBox() {
    var modal = $("#disconnected-box");
    var message_text = $("#disconnected-message");
    var spinner = SpinnerWidget("#disconnected-spinner");

    modal.modal({
      backdrop: "static",
      keyboard: false,
      show: true,
    });

    function show(message) {
      message_text.text(message);
      spinner.start();
      modal.modal("show");
    }

    show("Connecting...");

    return {
      show: show,
      hide: function () {
        modal.modal("hide");
        spinner.stop();
      },
    };
  }

  function BatteryIndicator() {
    var LOW_THRESHOLD = 5; // TODO check this
    var LOW_ICON = "fa-battery-quarter";
    var NORMAL_ICON = "fa-battery-full";
    var LOW_HIGHLIGHT = "battery-low";

    var icon = $("#battery-icon");
    var text = $("#battery-text");

    function setNormal() {
      icon.removeClass(LOW_ICON);
      icon.addClass(NORMAL_ICON);
      icon.removeClass(LOW_HIGHLIGHT);
      text.removeClass(LOW_HIGHLIGHT);
    }

    function setLow() {
      icon.removeClass(NORMAL_ICON);
      icon.addClass(LOW_ICON);
      icon.addClass(LOW_HIGHLIGHT);
      text.addClass(LOW_HIGHLIGHT);
    }

    function disconnected() {
      setNormal();
      text.text("?");
    }

    return {
      set: function (level) {
        text.text(level);
        if (level < LOW_THRESHOLD) {
          setLow();
        } else {
          setNormal();
        }
      },
      disconnected: disconnected,
    };
  }

  function Camera() {
    var STATIC = "static.gif";
    var image = $("#camera-snapshot");
    var spinner = SpinnerWidget("#camera-images");
    var snapshot = RateLimit(2000, function () {
      socket.snapshot();
      spinner.start();
      timer.restart();
    });
    var timer = Timer(snapshot.call, 30000);

    $("#camera-button").click(snapshot.call);
    $("#camera-overlay").click(snapshot.call);

    return {
      snapshot: snapshot.call,
      gotSnapshot: function (data) {
        // data is a base64-encoded image
        image.attr("src", "data:image/jpeg;base64," + data);
        spinner.stop();
      },
      disconnected: function () {
        image.attr("src", STATIC);
        spinner.stop();
        timer.stop();
        snapshot.reset();
      },
    };
  }

  function HeadControl() {
    var slider = $("#head-slider");
    var trigger = RateLimit(500, function () {
      socket.beginCmd(HEAD_TURN, slider.slider("value"));
    });

    slider.slider({
      orientation: "horizontal",
      min: -1,
      max: 1,
      value: 0,
      step: 0.01,
      slide: trigger.call,
      change: trigger.call,
      stop: function () {
        slider.slider("value", 0);
        socket.stop();
      },
    });

    return {
      disconnected: function () {
        slider.slider("value", 0);
        trigger.reset();
      },
    };
  }

  function DriveControl() {
    var RADIUS = 180;

    var trigger = RateLimit(500, function (evt, data) {
      var angle = data.angle.radian;
      var distance = data.distance;
      var x = (distance * Math.cos(angle)) / RADIUS;
      var y = (distance * Math.sin(angle)) / RADIUS;

      if (Math.abs(y) > 0.1) {
        socket.beginCmd(DRIVE, y);
      }

      if (Math.abs(x) > 0.1) {
        socket.beginCmd(TURN, x);
      }
    });

    // eslint-disable-next-line no-undef
    var joystick_manager = nipplejs.create({
      zone: $("#drive-control")[0],
      restOpacity: 1.0,
      size: 2 * RADIUS,
      position: {
        left: RADIUS + "px",
        top: RADIUS + "px",
      },
      mode: "static",
    });

    // There doesn't seem to be a proper way to customise the UI, so force it
    $(joystick_manager.get(0).ui.back).removeAttr("style");
    $(joystick_manager.get(0).ui.front).removeAttr("style");
    $(joystick_manager.get(0).ui.front).addClass("drive-control-handle");
    $(joystick_manager.get(0).ui.front).addClass("ui-slider-handle");
    $(joystick_manager.get(0).ui.front).addClass("ui-state-default");

    joystick_manager.on("move", trigger.call);
    joystick_manager.on("end", function () {
      socket.stop();
    });

    return {
      disconnected: function () {
        trigger.reset();
      },
    };
  }

  function VoiceControl() {
    var dropdown = $("#speech-dropdown");
    dropdown.selectmenu({
      // Doing it in CSS doesn't seem to work
      width: "78%",
    });

    var trigger = RateLimit(2000, function () {
      socket.playSound(dropdown.val());
    });

    $("#speech-button").click(trigger.call);

    return {
      disconnected: function () {
        trigger.reset();
      },
    };
  }

  function KeyHandler(down, up, repeat) {
    var pressed = false;
    var rate_limiter = RateLimit(500, function () {
      if (!pressed || repeat) {
        down();
      }
      pressed = true;
    });

    return {
      down: rate_limiter.call,
      up: function () {
        if (up) {
          up();
        }
        pressed = false;
        rate_limiter.reset();
      },
      disconnected: function () {
        rate_limiter.reset();
      },
    };
  }

  function CommandKey(command, value) {
    return KeyHandler(
      function () {
        socket.beginCmd(command, value);
      },
      function () {
        socket.releaseCmd(command, value);
      },
      true,
    );
  }

  function OneOffKey(down) {
    return KeyHandler(down, null, false);
  }

  function Keyboard(handlers) {
    var connected = false;

    $(document).keydown(function (event) {
      if (
        connected &&
        event.target === document.body &&
        event.which in handlers
      ) {
        handlers[event.which].down();
      }
    });

    $(document).keyup(function (event) {
      if (
        connected &&
        event.target === document.body &&
        event.which in handlers
      ) {
        handlers[event.which].up();
      }
    });

    return {
      connected: function () {
        connected = true;
      },
      disconnected: function () {
        connected = false;
        for (var key in handlers) {
          if (Object.prototype.hasOwnProperty.call(handlers, key)) {
            handlers[key].disconnected();
          }
        }
      },
    };
  }

  DialogBox("#btn-about", "#about-box", "#about-box-close");
  DialogBox("#btn-battery", "#battery-box", "#battery-box-close");

  var disconnected_box = DisconnectedBox();
  var battery_indicator = BatteryIndicator();

  var camera = Camera();
  var head_control = HeadControl();
  var drive_control = DriveControl();
  var voice_control = VoiceControl();

  var keyboard = Keyboard({
    87: CommandKey(DRIVE, 1.0), // W
    83: CommandKey(DRIVE, -1.0), // S
    65: CommandKey(TURN, -1.0), // A
    68: CommandKey(TURN, 1.0), // D
    81: CommandKey(HEAD_TURN, -1.0), // Q
    69: CommandKey(HEAD_TURN, 1.0), // E
    86: OneOffKey(function () {
      socket.toggleVerbose();
    }), // V
    76: OneOffKey(function () {
      socket.toggleLights();
    }), // L
    13: OneOffKey(function () {
      camera.snapshot();
    }), // Return
  });

  var socket = Socket({
    ready: function () {
      disconnected_box.hide();
      keyboard.connected();
      camera.snapshot();
    },
    busy: function () {
      disconnected_box.show(
        "Someone else is already connected to the Dalek. Trying to connect...",
      );
    },
    disconnected: function () {
      battery_indicator.disconnected();
      camera.disconnected();
      head_control.disconnected();
      drive_control.disconnected();
      voice_control.disconnected();
      keyboard.disconnected();
      disconnected_box.show(
        "Lost connection to the Dalek. Trying to reconnect...",
      );
    },
    snapshot: function (data) {
      camera.gotSnapshot(data);
    },
    battery: function (battery) {
      battery_indicator.set(battery);
    },
  });
});
