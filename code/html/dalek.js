$(document).ready(function() {
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

    DialogBox("#btn-about", "#about-box", "#about-box-close");
    DialogBox("#btn-battery", "#battery-box", "#battery-box-close");

    var disconnected_box = DisconnectedBox();
    var battery_indicator = BatteryIndicator();

    var socket = Socket({
        ready: function() {
            disconnected_box.hide();
            camera.snapshot();
        },
        busy: function() {
            disconnected_box.show("Someone else is already connected to the Dalek. Trying to connect...");
        },
        disconnected: function() {
            battery_indicator.disconnected();
            camera.disconnected();
            disconnected_box.show("Lost connection to the Dalek. Trying to reconnect...");
        },
        snapshot: function(data) {
            camera.gotSnapshot(data);
        },
        battery: function(battery) {
            battery_indicator.set(battery);
        }
    });

    camera = Camera();


    var keyboard = Keyboard({
        87: CommandKey(DRIVE, 1.0), // W
        83: CommandKey(DRIVE, -1.0), // S
        65: CommandKey(TURN, -1.0), // A
        68: CommandKey(TURN, 1.0), // D
        81: CommandKey(HEAD_TURN, -1.0), // Q
        69: CommandKey(HEAD_TURN, 1.0), // E
        86: OneOffKey(function() { socket.toggleVerbose(); }), // V
        76: OneOffKey(function() { socket.toggleLights(); }), // L
        13: OneOffKey(function() { camera.snapshot(); }), // Return
    });

    var drive_control = DriveControl();
    // var head_control = HeadControl();

    $("#button-foobar").click(function() {
        socket.exit();
    });

    $("#button-speak").click(function() {
        socket.playSound($("#speak-text").val());
    });

    $("#button-snapshot").click(function() {
        socket.snapshot();
    });
// SOUND_DICT = {pygame.K_1: "exterminate",
//               pygame.K_2: "gun",
//               pygame.K_3: "exterminate-exterminate-exterminate",
//               pygame.K_4: "doctor",
//               pygame.K_5: "the-doctor",
//               pygame.K_6: "it-is-the-doctor",
//               pygame.K_7: "the-doctor-must-die",
//               pygame.K_8: "identify-yourself",
//               pygame.K_9: "report",
//               pygame.K_0: "explain",
//               pygame.K_F1: "cease-talking",
//               pygame.K_F2: "social-interaction-will-cease",
//               pygame.K_F3: "daleks-are-supreme",
//               pygame.K_F4: "you-would-make-a-good-dalek",
//               pygame.K_F5: "you-will-follow",
//               pygame.K_F6: "you-will-identify",
//               pygame.K_F7: "daleks-do-not-question-orders",
//               pygame.K_F8: "why",
//               pygame.K_F9: "that-is-incorrect",
//               pygame.K_F10: "bring-him-to-me",
//               pygame.K_F11: "which-of-you-is-least-important",
//               pygame.K_F12: "would-you-care-for-some-tea",
//               pygame.K_LEFTBRACKET: "i-bring-you-the-human",
//               pygame.K_RIGHTBRACKET: "your-loyalty-will-be-rewarded",
//               pygame.K_MINUS: "you-will-be-necessary",
//               pygame.K_EQUALS: "daleks-have-no-concept-of-worry",
//               pygame.K_BACKQUOTE: "this-human-is-our-best-option",
//               pygame.K_SEMICOLON: "can-i-be-of-assistance",
//               pygame.K_QUOTE: "please-excuse-me",
//               pygame.K_HASH: "i-have-duties-to-perform",
//               pygame.K_p: "then-hear-me-talk-now"}

// RANDOM_SOUNDS = ["exterminate",
//                  "gun",
//                  "exterminate-exterminate-exterminate",
//                  "report",
//                  "social-interaction-will-cease",
//                  "you-would-make-a-good-dalek",
//                  "would-you-care-for-some-tea",
//                  "explain",
//                  "cease-talking",
//                  "daleks-are-supreme",
//                  "you-will-identify",
//                  "the-doctor-must-die"]


// class Main(object):

//     FRAME_RATE = 60
//     TICK_LENGTH_SECONDS = 1.0 / float(FRAME_RATE)
//     REPEAT_TIME_SECONDS = 5

//     def __init__(self, addr, snapshot_file):
//         super(Main, self).__init__()
//         self.screen = pygame.display.set_mode((1000, 480))
//         pygame.display.set_caption("Dalek")
//         pygame.display.set_icon(pygame.image.load("dalek.ico").convert_alpha())
//         self.background = pygame.image.load("background.png").convert()
//         self.overlay = pygame.image.load("overlay.png").convert_alpha()
//         self.font = pygame.font.Font(None, 60)
//         self.screen_text = ""

//         self.battery_font = pygame.font.Font(None, 20)
//         self.battery_text = ""
//         def battery_handler(data):
//             self.battery_text = data

//         self.snapshot = None
//         def snapshot_handler(data):
//             image = PIL.Image.open(io.BytesIO(data)).rotate(90)
//             image.save(snapshot_file, "JPEG")
//             image = image.resize((360, int(image.size[1] * (360.0/image.size[0]))))
//             self.snapshot = pygame.image.fromstring(image.tobytes(), image.size, image.mode)

//         self.controller = RemoteController(addr, snapshot_handler, battery_handler)
//         self.drive_queue = EventQueue()
//         self.other_queue = EventQueue()

//         self.random_mode = False
//         self.random_flash_timer = 0
//         self.random_show_text = False

//         try:
//             self.main_loop()
//         finally:
//             self.controller.exit()

//     def begin_cmd_action(self, cmd, value, repeat):
//         def action():
//             self.controller.begin_cmd(cmd, value)

//         if repeat:
//             return RepeatingAction(Main.REPEAT_TIME_SECONDS, action, Main.TICK_LENGTH_SECONDS)
//         else:
//             return action

//     def release_cmd_action(self, cmd, value):
//         def action():
//             self.controller.release_cmd(cmd, value)
//         return action

//     def timed_key_press_action(self, seconds, cmd, value):
//         return DurationAction(seconds,
//                               self.begin_cmd_action(cmd, value, False),
//                               self.release_cmd_action(cmd, value),
//                               Main.TICK_LENGTH_SECONDS)

//     def stop_action(self):
//         def action():
//             self.controller.stop()
//         return action

//     def start_random_mode(self):
//         if not self.random_mode:
//             self.random_mode = True
//             self.controller.stop()
//             self.drive_queue.clear()
//             self.other_queue.clear()
//             self.drive_queue.add(RandomModeAction(self))
//             self.screen_text = "Random mode"
//             self.random_flash_timer = 0
//             self.random_show_text = True

//     def maybe_stop_random_mode(self, manual):
//         if self.random_mode and manual:
//             self.random_mode = False
//             self.controller.stop()
//             self.drive_queue.clear()
//             self.other_queue.clear()
//             self.screen_text = ""
//             self.random_show_text = False


//     def begin_drive_cmd(self, cmd, value, repeat, manual=True):
//         self.maybe_stop_random_mode(manual)
//         self.drive_queue.replace(self.begin_cmd_action(cmd, value, repeat))

//     def release_drive_cmd(self, cmd, value, manual=True):
//         self.maybe_stop_random_mode(manual)
//         self.drive_queue.replace(self.release_cmd_action(cmd, value))

//     def begin_head_cmd(self, cmd, value, manual=True):
//         self.maybe_stop_random_mode(manual)
//         self.other_queue.add(self.begin_cmd_action(cmd, value, False))

//     def release_head_cmd(self, cmd, value, manual=True):
//         self.maybe_stop_random_mode(manual)
//         self.other_queue.add(self.release_cmd_action(cmd, value))

//     def main_loop(self):
//         // Take a snapshot to start things off
//         self.controller.snapshot()

//         while True:
//             for event in pygame.event.get():
//                 if event.type == pygame.QUIT:
//                     return
//                 elif event.type == pygame.KEYDOWN:
//                     if event.key == pygame.K_ESCAPE:
//                         return
//                     elif event.key == pygame.K_w:
//                         self.begin_drive_cmd(DRIVE, 1.0, True)
//                     elif event.key == pygame.K_s:
//                         self.begin_drive_cmd(DRIVE, -1.0, True)
//                     elif event.key == pygame.K_a:
//                         self.begin_drive_cmd(TURN, -1.0, True)
//                     elif event.key == pygame.K_d:
//                         self.begin_drive_cmd(TURN, 1.0, True)
//                     elif event.key == pygame.K_q:
//                         self.begin_head_cmd(HEAD_TURN, -1.0)
//                     elif event.key == pygame.K_e:
//                         self.begin_head_cmd(HEAD_TURN, 1.0)
//                     elif event.key == pygame.K_RETURN:
//                         self.controller.snapshot()
//                     elif event.key == pygame.K_v:
//                         self.controller.toggle_verbose()
//                     elif event.key == pygame.K_l:
//                         self.controller.toggle_lights()
//                     elif event.key == pygame.K_SPACE:
//                         self.start_random_mode()
//                     elif event.key in SOUND_DICT:
//                         self.controller.play_sound(SOUND_DICT[event.key])
//                 elif event.type == pygame.KEYUP:
//                     if event.key == pygame.K_w:
//                         self.release_drive_cmd(DRIVE, 1.0)
//                     elif event.key == pygame.K_s:
//                         self.release_drive_cmd(DRIVE, -1.0)
//                     elif event.key == pygame.K_a:
//                         self.release_drive_cmd(TURN, -1.0)
//                     elif event.key == pygame.K_d:
//                         self.release_drive_cmd(TURN, 1.0)
//                     elif event.key == pygame.K_q:
//                         self.release_head_cmd(HEAD_TURN, -1.0)
//                     elif event.key == pygame.K_e:
//                         self.release_head_cmd(HEAD_TURN, 1.0)

//             self.drive_queue.process()
//             self.other_queue.process()

//             self.screen.fill((0, 0, 0))
//             self.screen.blit(self.background, (360, 0))

//             if self.snapshot:
//                 self.screen.blit(self.snapshot, (0, (480 - self.snapshot.get_height())/2))
//             self.screen.blit(self.overlay, (0, 0))

//             if self.random_mode:
//                 self.random_flash_timer += 1

//                 if self.random_flash_timer >= 1 * Main.FRAME_RATE:
//                     self.random_show_text = not self.random_show_text
//                     self.random_flash_timer = 0

//                 if self.random_show_text:
//                     disp = self.font.render(self.screen_text, True, (255, 0, 0))
//                     rect = disp.get_rect()
//                     rect.left = 630
//                     rect.top = 220
//                     self.screen.blit(disp, rect)

//             if self.battery_text:
//                 disp = self.battery_font.render(self.battery_text, True, (0, 0, 0))
//                 rect = disp.get_rect()
//                 rect.left = 940
//                 rect.top = 9
//                 self.screen.blit(disp, rect)

//             pygame.display.flip()
//             time.sleep(1/float(Main.FRAME_RATE))


// class RandomModeAction(object):
//     def __init__(self, parent):
//         super(RandomModeAction, self).__init__()
//         self.parent = parent
//         self.timer = 0
//         self.set_timer(10)
//         self.snapshot_timer = 0

//     def set_timer(self, min_time):
//         min_time = int(min_time)
//         self.timer = random.randint((min_time + 3) * Main.FRAME_RATE, (min_time + 5) * Main.FRAME_RATE)
//         print "Random timer: %f s (%d ticks)" % (self.timer / float(Main.FRAME_RATE), self.timer)

//     def random_drive_action(self, cmd):
//         length = random.uniform(3, 10)
//         self.parent.drive_queue.add(self.parent.timed_key_press_action(length,
//                                                                        cmd,
//                                                                        random.choice([-0.5, 0.5])))
//         return length

//     def random_head_action(self):
//         length = random.uniform(1, 5)
//         self.parent.other_queue.add(self.parent.timed_key_press_action(length,
//                                                                        HEAD_TURN,
//                                                                        random.choice([-1, 1])))
//         return length

//     def random_speech(self):
//         self.parent.controller.play_sound(random.choice(RANDOM_SOUNDS))
//         return 5

//     def __call__(self):
//         self.snapshot_timer += 1
//         if self.snapshot_timer >= 120 * Main.FRAME_RATE:
//             self.parent.controller.snapshot()
//             self.snapshot_timer = 0

//         if self.timer <= 0:
//             choice = random.randint(0, 99)
//             length = 0
//             if choice < 25:
//                 length = self.random_head_action()
//             elif choice < 50:
//                 length = self.random_drive_action(DRIVE)
//             elif choice < 75:
//                 length = self.random_drive_action(TURN)
//             else:
//                 length = self.random_speech()

//             self.set_timer(length)
//         else:
//             self.timer -= 1
//         return True


// pygame.init()

// parser = argparse.ArgumentParser(description="Control the Dalek remotely from another machine")
// parser.add_argument("addr", help="Address of the Dalek")
// parser.add_argument("snapshotFile", help="File in which to save snapshots")

// args = parser.parse_args()

// Main(args.addr, args.snapshotFile)
// sys.exit(0)






    function KeyHandler(down, up, repeat) {
        var pressed = false;
        var press_time = 0;
        var REPEAT_TIME_MSEC = 5000;

        function shouldRepeat() {
            // To avoid spamming, we repeat a keypress only every few seconds
            return (repeat &&
                    timeSince(press_time) > REPEAT_TIME_MSEC);
        }

        return {
            down: function() {
                if (!pressed || shouldRepeat()) {
                    if (down) {
                        down();
                    }
                    press_time = new Date().getTime();
                }
                pressed = true;
            },
            up: function() {
                if (up) {
                    up();
                }
                pressed = false;
            }
        }
    }

    function CommandKey(command, value) {
        return KeyHandler(
            function() {
                socket.beginCmd(command, value);
            },
            function() {
                socket.releaseCmd(command, value);
            },
            true
        );
    }

    function OneOffKey(down) {
        return KeyHandler(down, null, false);
    }

    function Keyboard(handlers) {
        $(document).keydown(function(event) {
            if (event.which in handlers) {
                handlers[event.which].down();
            }
        });

        $(document).keyup(function(event) {
            if (event.which in handlers) {
                handlers[event.which].up();
            }
        });
    }


    function DriveControl() {
        var RADIUS = 200;
        var RATE_LIMIT = 500;
        var last_sent = 0;

        var joystick_manager = nipplejs.create({
            zone: $("#foobar")[0],
            color: "#00ffff",
            position: { top: "300px", left: "300px" },
            size: 2 * RADIUS,
            mode: "static"
        });

        var last_x = 0;
        var last_y = 0;

        joystick_manager.on("move", function(evt, data) {
            if (timeSince(last_sent) > RATE_LIMIT) {
                var angle = data.angle.radian;
                var distance = data.distance;
                var x = distance * Math.cos(angle) / RADIUS;
                var y = distance * Math.sin(angle) / RADIUS;

                if (Math.abs(y) > 0.1) {
                    socket.beginCmd(DRIVE, y);
                    last_y = y;
                }

                if (Math.abs(x) > 0.1) {
                    socket.beginCmd(TURN, x);
                    last_x = x;
                }

                last_sent = new Date().getTime();
            }
        });

        joystick_manager.on("end", function() {
            socket.stop();
        });
    }

    function HeadControl() {
        var slider = $("#head-slider");

        slider.slider({
            orientation: "horizontal",
            min: -1,
            max: 1,
            value: 0,
            step: 0.01,
            slide: function(event, ui) {
                socket.beginCmd(HEAD_TURN, slider.slider("value"));
            },
            change: function(event, ui) {
                socket.beginCmd(HEAD_TURN, slider.slider("value"));
            },
            stop: function(event, ui) {
                slider.slider("value", 0);
                socket.stop();
            }
        });
    }




    
    function timeSince(time) {
        return new Date().getTime() - time;
    }

    function DialogBox(trigger_id, box_id, close_button_id) {
        var modal = $(box_id);
        var close = $(close_button_id);

        modal.modal({
            backdrop: "static",
            keyboard: false,
            show: false
        });

        $(trigger_id).click(function() {
            modal.modal("show");
        });

        close.click(function() {
            modal.modal("hide");
        });
    }

    function DisconnectedBox() {
        var modal = $("#disconnected-box");
        var message_text = $("#disconnected-message");
        var spinner = new Spinner({
            color:"#3d86cb",
            lines: 12,
        });

        modal.modal({
            backdrop: "static",
            keyboard: false,
            show: true
        });

        function show(message) {
            message_text.text(message);
            spinner.spin($("#disconnected-spinner")[0]);
            modal.modal("show");
        }

        show("Connecting...");

        return {
            show: show,
            hide: function() {
                modal.modal("hide");
                spinner.stop();
            }
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
            set: function(level) {
                text.text(level);
                if (level < LOW_THRESHOLD) {
                    setLow();
                } else {
                    setNormal();
                }
            },
            disconnected: disconnected
        };
    }

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
                    } else if (cmd === BATTERY && state === STATE_READY && args.length > 0) {
                        callbacks.battery(args[0]);
                    } else if (cmd === SNAPSHOT && state === STATE_READY && args.length > 0) {
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
            toggleVerbose: function() {
                verbose = !verbose;
            },
            beginCmd: function(cmd, value) {
                send(BEGIN, cmd, value);
            },
            releaseCmd: function(cmd, value) {
                send(RELEASE, cmd, value);
            },
            stop: function() {
                send(STOP);
            },
            playSound: function(sound) {
                send(PLAY_SOUND, sound);
            },
            stopSound: function() {
                send(STOP_SOUND);
            },
            snapshot: function() {
                send(SNAPSHOT);
            },
            toggleLights: function() {
                send(TOGGLE_LIGHTS);
            },
            exit: function() {
                send(EXIT);
                socket.close();
            }
        };
    }

    function Camera() {
        var STATIC = "static.gif";
        var image = $("#camera-snapshot");
        var spinner = new Spinner({
            color:"#3d86cb",
            lines: 12,
            radius: 40,
            length: 50,
            width: 14,
            corners: 1
        });

        function snapshot() {
            socket.snapshot();
            spinner.spin($("#camera-images")[0]);
        }

        $("#camera-button").click(snapshot);
        $("#camera-overlay").click(snapshot);

        return {
            snapshot: snapshot,
            gotSnapshot: function(data) {
                // data is a base64-encoded image
                image.attr("src", "data:image/jpeg;base64," + data);
                spinner.stop();
            },
            disconnected: function() {
                image.attr("src", STATIC);
                spinner.stop();
            }
        };
    }
});
